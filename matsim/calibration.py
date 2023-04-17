#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import glob
import math
import shutil
import sys
from os import path, makedirs
from time import sleep

from typing import Any, Union, Sequence, Dict, Callable, Tuple

import yaml
import numpy as np
import pandas as pd
import geopandas
import optuna

from optuna.trial import TrialState

# This is there so that this file can be used standalone, as well as installed from the package
try:
    import analysis
except ImportError:
    from . import analysis

def _completed_trials(study):
    completed = filter(lambda s: s.state == TrialState.COMPLETE, study.trials)
    return sorted(completed, key=lambda s: s.number)

def _same_sign(x):
    x = x.to_numpy()
    return np.all(x >= 0) if x[0] >= 0 else np.all(x < 0)

def positive_constraint(mode, val):
    """ Ensures parameter are positive """
    return max(0, val)

def negative_constraint(mode, val):
    """ Ensure parameter are negative """
    return min(0, val)

class CalibrationSampler(optuna.samplers.BaseSampler):
    """ Sample asc according to obtained mode shares """

    def __init__(self, target, mode_share, fixed_mode, initial, lr, constraints):

        self.target = target
        self.mode_share = mode_share
        self.fixed_mode = fixed_mode
        self.initial = initial
        self.lr = lr
        self.constraints = constraints
    
    def infer_relative_search_space(self, study, trial):
        return {}

    def sample_relative(self, study, trial, search_space):
        #study._storage.set_trial_system_attr(trial._trial_id, "search_space", self._search_space)
        return {}

    def sample_independent(self, study, trial, param_name, param_distribution):

        param, _, mode = param_name.partition("_")

        completed = _completed_trials(study)
        if len(completed) == 0:
            initial = self.initial.get(param, {}).get(mode, 0)

            if self.constraints is not None and param in self.constraints:
                initial = self.constraints[param](mode, initial)

            return initial

        last = completed[-1]
        last_param = last.params[param_name]

        if param == "asc":
            step = self.sample_asc(mode, last)
        elif param == "dist":
            step = self.sample_dist_util(mode, last)

        rate = 1.0
        if self.lr is not None:

            rate = self.lr(float(len(completed) + 1), param_name, step, self.mode_share, trial, study)

            # rate of None or 0 would be invalid
            if not rate:
                rate = 1

            # numpy types need casting
            rate = float(rate)

        trial.set_user_attr("%s_rate" % param_name, rate)
        trial.set_user_attr("%s_step" % param_name, step)

        last_param += rate * step

        # Call constraint if present
        if self.constraints is not None and param in self.constraints:
            last_param = self.constraints[param](mode, last_param)

        return last_param

    def sample_asc(self, mode, last):
        
        if mode == self.fixed_mode:
            return 0

        step = self.calc_asc_update(self.mode_share.loc[mode].share, last.user_attrs["%s_share" % mode],
                        self.mode_share.loc[self.fixed_mode].share, last.user_attrs["%s_share" % self.fixed_mode])
        
        return step

    def sample_dist_util(self, mode, last):
        
        df = pd.DataFrame.from_dict(last.user_attrs["mode_stats"], orient="tight")
        target = self.target[self.target["mode"] == mode].reset_index(drop=True).copy()

        df = df.loc[target.dist_group].reset_index()

        # Trips distances shares over all modes
        # Correction factor is calculated here
        ref_dist = self.target.groupby("dist_group").agg(share=("share", "sum"))
        sim_dist = df.groupby("dist_group").agg(share=("share", "sum"))

        correction = ref_dist.loc[target.dist_group] / sim_dist.loc[target.dist_group]

        df = df[df.main_mode == mode].reset_index(drop=True).copy()

        if "mean_dist" not in target.columns:
            target["mean_dist"] = df.mean_dist

        df["correction"] = correction.values

        target.share = target.share / sum(target.share)
        df.share = df.share / sum(df.share)

        real = (df.mean_dist * df.share * df.correction).sum()
        target = (target.mean_dist * target.share).sum()

        # TODO: magnitude should depend on the asc

        # TODO: configurable parameter
        return float(0.05 * (target - real) / (1000 * 1000))

    @staticmethod
    def calc_asc_update(z_i, m_i, z_0, m_0):
        """ Calculates the asc update for one step """
        # Update asc
        # (1) Let z_i be the observed share of mode i. (real data, to be reproduced)
        # (2) Run the simulation to convergence. Obtain simulated mode shares m_i.
        # (3) Do nothing for mode 0. For all other modes: add [ln(z_i) - ln(m_i)] – [ln(z_0) - ln(m_0)] to its ASC.
        # (4) Goto 2.
        return math.log(z_i) - math.log(m_i) - (math.log(z_0) - math.log(m_0))

def calc_adjusted_mode_share(sim: pd.DataFrame, survey: pd.DataFrame, 
                             count_var: str = "trips", dist_var: str = "dist_group") -> Tuple[Any, pd.DataFrame]:
    """ This function can be used if the given input trip data has a different distance distribution than the survey data.
        It will rescale the survey data to match simulated data, which allows to calculate an adjusted overall mode share.

        :param sim: data frame containing shares for distance group and modes
        :param survey: data frame containing shares from survey data
        :param count_var: name of column containing the number of trips or share in 'sim'
        :param dist_var: name of the column holding the distance group information
        :return: tuple of optimization result and adjusted mode share
    """
    from scipy.optimize import minimize

    sagg = sim.groupby(dist_var).sum()
    sagg['share'] = sagg[count_var] / np.sum(sagg[count_var])

    # Rescale the distance groups of the survey data so that it matches the distance group distribution of the simulation
    # The overall mode share after this adjustment will the resulting adjusted mode share
    def f(x, result=False):
        adj = survey.copy()

        for i, t in enumerate(x):
            adj.loc[adj[dist_var] == sagg.index[i], "share"] *= t

        adj.share = adj.share / np.sum(adj.share)

        agg = adj.groupby(dist_var).sum()

        # Minimized difference between adjusted and simulated distribution
        err = sum((sagg.share - agg.share)**2)

        if result:
            return adj

        return err

    # One variable for each distance group
    x0 = np.ones(len(sagg.index)) / len(sagg.index)

    # Sum should be less than one
    cons = [{'type': 'ineq', 'fun': lambda x:  1 - sum(x)}]
    bnds = tuple((0, 1) for x in x0)

    res = minimize(f, x0, method='SLSQP', bounds=bnds, constraints=cons)

    df = f(res.x, True)

    return res, df


def study_as_df(study):
    """ Convert study to dataframe """
    completed = _completed_trials(study)

    modes = study.user_attrs["modes"]
    #fixed_mode = study.user_attrs["fixed_mode"]

    data = []

    for i, trial in enumerate(completed):

        for j, m in enumerate(modes):
            entry = {
                "trial": i,
                "mode": m,
                "asc": trial.params[m],
                "error": trial.values[j]
            }

            for k, v in trial.user_attrs.items():
                if k.startswith(m + "_"):
                    entry[k[len(m) + 1:]] = v

            data.append(entry)

    return pd.DataFrame(data)

def auto_lr_scheduler(start=9, interval=3, lookback=3, throttle=0.7):
    """ Creates a function to be passed into the lr argument of the mode share study. This scheduler will
        try to increase the step size automatically to speed up convergence. 
        
        :param start: earliest run to start adjusting
        :param interval: apply every x runs
        :param lookback: look at x recent runs for the interpolation
        :param throttle: reduce estimate as step size will most likely be over-estimated
        """
    if start < 1:
        raise ValueError("Start must be at least 1")

    if interval > start:
        raise ValueError("Start must be less equal than interval")
            
    def _fn(n, mode, update, mode_share, trial, study):
    
        if n < start:
            return 1
        
        # Only run every x iterations
        if (n - start) % interval != 0:
            return 1
        
        df = study_as_df(study)        
        df = df[df["mode"] == mode]
    
        updates = df.asc.diff(1)
        changes = df.share.diff(1)

        # ensure that all previous updates and all previous reactions have been in the same direction
        # otherwise there will be instability
        if not _same_sign(updates.iloc[-lookback:]) or not _same_sign(changes.iloc[-lookback:]):
            return 1
                
        asc = df.asc.iloc[-1]
    
        x = df.share.iloc[-lookback:]
        y = df.asc.iloc[-lookback:]
        
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    
        target = m*mode_share[mode] + c        
        new_update = (target - asc) * throttle
        
        # updates must be in same direction
        if np.sign(update) != np.sign(new_update):
            return 1
        
        trial.set_user_attr("%s_auto_lr" % mode, True)

        return new_update / update


    return _fn

def default_chain_scheduler(completed):
    """ Default function to determin when to chain runs. """

    n = len(completed)

    if n <= 6:
        return n % 2 == 0
    
    if n <= 15:
        return n % 5 == 0

    if n <= 50:
        return n % 10 == 0

    return False

def linear_lr_scheduler(start=0.6, end=1, interval=3):
    """ Creates an lr scheduler that will interpolate linearly from start to end over the first n iterations.

        :param start: Initial learning rate.
        :param end: Finial learning rate to reach.
        :param interval: Number of runs until end rate should be reached.
    """
    if interval < 2:
        raise ValueError("N must be greater or equal 2.")

    def _fn(n, *args, **kwargs):
        
        if n > interval:
            return end

        return start + (n - 1) * (end - start) / interval

    return _fn

def create_mode_calibration_study(name: str,  params: set,
                            jar: Union[str, os.PathLike], config: Union[str, os.PathLike],
                            modes: Sequence[str], target: Union[str, os.PathLike],
                            fixed_mode: str = "walk",
                            args: Union[str, Callable]="", jvm_args="",
                            initial_params: Dict[str, Dict[str, float]] = None,
                            transform_persons: Callable = None,
                            transform_trips: Callable = None,
                            chain_runs: Union[bool, int, Callable] = False,
                            lr: Callable[[int, str, float, Dict[str, float], optuna.Trial, optuna.Study], float] = None,
                            constraints: Dict[str, Callable[[str, float], float]] = None,
                            storage: optuna.storages.RDBStorage = None,
                            debug: bool = False
                            ) -> Tuple[optuna.Study, Callable]:
    """ Create or load an existing study for mode share calibration using asc values.

    This function returns the study and optimization objective as tuple. Which can be used like this:
        study.optimize(obj, 10)

    :param name: name of the study
    :param params: parameters to calibrate
    :param jar: path to executable jar file of the scenario
    :param config: path to config file to run
    :param modes: list of all relevant modes
    :param target: csv file with target shares
    :param fixed_mode: the fixed mode with asc=0
    :param args: additional arguments to the executable jar, can also be a callback function
    :param jvm_args: additional jvm args
    :param initial_asc: dict of initial asc values
    :param transform_persons: callable to filter persons included in mode share
    :param transform_trips: callable to modify trips included in mode share
    :param chain_runs: automatically use the output plans of each run as input for the next, either True or number of iterations or callable
    :param lr: learning rate schedule, will be called with (trial number, mode, asc update, mode_share, trial, study)
    :param constraints: constraints for each mode, must return asc and will be called with original asc
    :param storage: custom storage object to overwrite default sqlite backend
    :param debug: enable debug output
    :return: tuple of study and optimization objective.
    """

    # Init with 0
    if initial_params is None:
        for p in params:
            for m in modes:
                initial_params[m] = 0

    # Set some custom arguments to prevent known errors on NFS
    if storage is None:
        storage = optuna.storages.RDBStorage(url="sqlite:///%s.db" % name, 
            engine_kwargs={"connect_args": {"timeout": 100}, "isolation_level": "AUTOCOMMIT"})
        
    target = pd.read_csv(target)

    mode_share = target.groupby("mode").agg(share=("share", "sum"))

    study = optuna.create_study(
            study_name=name, 
            storage=storage, 
            load_if_exists=True,
            directions=["minimize"] * len(modes),
            sampler=CalibrationSampler(target, mode_share, fixed_mode, initial_params, lr, constraints)
        )

    study.set_user_attr("modes", modes)
    study.set_user_attr("params", params)
    study.set_user_attr("fixed_mode", fixed_mode)

    if not path.exists("params"):
        makedirs("params")

    if not path.exists("runs"):
        makedirs("runs")

    print("Running study with target:", mode_share)

    def f(trial):

        params_path = path.join("params", "run%d.yaml" % trial.number)
        mode_params = []

        for mode in modes:
            # preserve order
            m = {"mode": mode}

            if "asc" in params:
                m["constant"] = trial.suggest_float("asc_" + mode, sys.float_info.min, sys.float_info.max)

            if "util_dist" in params or "dist" in params:
                m["marginalUtilityOfDistance_util_m"] = trial.suggest_float("dist_" + mode, sys.float_info.min, sys.float_info.max)

            mode_params.append(m)

        with open(params_path, "w") as f:
            yaml.dump({"planCalcScore": {"scoringParameters": [{"modeParams": mode_params}]}}, f, sort_keys=False)

        run_dir = "runs/%03d" % trial.number

        if os.path.exists(run_dir):
            shutil.rmtree(run_dir)

        completed = _completed_trials(study)

        # Call args if necesarry
        run_args = args(completed) if callable(args) else args

        cmd = "java %s -jar %s run --config %s --yaml %s --output %s --runId %03d %s" \
              % (jvm_args, jar, config, params_path, run_dir, trial.number, run_args)

        # Max fix extra whitespaces in args
        cmd = cmd.strip()

        if chain_runs:

            out = None
            for t in reversed(completed):
                out = glob.glob("runs/%03d/*.output_plans.xml.gz" % t.number)
                if out:
                    out = path.abspath(out[0])
                    break

            if out:
                last_chained = study.user_attrs.get("last_chained_run", None)
                if (chain_runs is True or
                            (callable(chain_runs) and chain_runs(completed)) or
                            (type(chain_runs) == int and len(completed) % chain_runs == 0)):
                    cmd += " --config:plans.inputPlansFile=" + out
                    study.set_user_attr("last_chained_run", out)

                elif last_chained:
                    cmd += " --config:plans.inputPlansFile=" + last_chained

            else:
                print("No output plans for chaining runs found.")

        # Extra whitespaces will break argument parsing
        cmd = cmd.strip()

        print("Running cmd %s" % cmd)

        if os.name != 'nt':
            cmd = cmd.split(" ")

        p = subprocess.Popen(cmd, 
                             stdout=sys.stdout if debug else subprocess.DEVNULL, 
                             stderr=sys.stderr if debug else subprocess.DEVNULL)
        try:    
            while p.poll() is None:
                sleep(1)

            if p.returncode != 0:
                raise Exception("Process returned with error code: %s" % p.returncode)
        finally:
            p.terminate()

        shares = analysis.calc_mode_share(run_dir, transform_persons=transform_persons, transform_trips=transform_trips)
        mode_stats = analysis.calc_mode_stats(run_dir, transform_persons=transform_persons, transform_trips=transform_trips)

        trial.set_user_attr("mode_stats", mode_stats.to_dict(orient="tight"))

        print("Obtained mode shares:", shares)

        for k, v in shares.items():
            trial.set_user_attr("%s_share" % k, v)

        res = []
        for mode in modes:
            res.append(abs(mode_share.loc[mode] - trial.user_attrs["%s_share" % mode]))

        return res

    return study, f

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Calibration CLI")
    parser.add_argument('file', nargs=1, type=str, help="Path to input db")
    parser.add_argument("--name", type=str, default="calib", help="Calibration name")
    parser.add_argument("--output", default=None, help="Output path")
    args = parser.parse_args()

    study = optuna.load_study(
            study_name=args.name, 
            storage="sqlite:///%s" % args.file[0],
    )

    if not args.output:
        args.output = args.file[0] + ".csv"

    df = study_as_df(study)
    df.to_csv(args.output, index=False)