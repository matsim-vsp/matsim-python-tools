#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Contains calibration related functions """

__all__ = ["create_calibration", "ASCCalibrator"]

import os
import shutil
import subprocess
import sys
from os import path, makedirs
from time import sleep
from typing import Union, Sequence, Callable

import optuna
import yaml
from optuna.trial import TrialState

from .analysis import *
from .base import CalibratorBase
from .calib_asc import ASCCalibrator


def _completed_trials(study):
    completed = filter(lambda s: s.state == TrialState.COMPLETE, study.trials)
    return sorted(completed, key=lambda s: s.number)


def _same_sign(x):
    x = x.to_numpy()
    return np.all(x >= 0) if x[0] >= 0 else np.all(x < 0)


class CalibrationSampler(optuna.samplers.BaseSampler):
    """ Run calibrators on obtained mode shares """

    def __init__(self, calibrators):
        self.calibrators = {c.name: c for c in calibrators}

    def infer_relative_search_space(self, study, trial):
        return {}

    def sample_relative(self, study, trial, search_space):
        # study._storage.set_trial_system_attr(trial._trial_id, "search_space", self._search_space)
        return {}

    def sample_independent(self, study, trial, param_name, param_distribution):

        prefix, _, param = param_name.partition("_")
        c : CalibratorBase = self.calibrators[prefix]

        completed = _completed_trials(study)
        if len(completed) == 0:
            initial = c.sample_initial(param)

            if c.constraints is not None and param in c.constraints:
                initial = c.constraints[param](param, initial)

            return initial

        last = completed[-1]
        last_param = last.params[param_name]

        step = c.update_step(param, last)

        rate = 1.0
        if c.lr is not None:

            rate = c.lr(float(len(completed) + 1), param_name, step, trial, study)

            # rate of None or 0 would be invalid
            if not rate:
                rate = 1

            # numpy types need casting
            rate = float(rate)

        trial.set_user_attr("%s_rate" % param_name, rate)
        trial.set_user_attr("%s_step" % param_name, step)

        last_param += rate * step

        # Call constraint if present
        if c.constraints is not None and param in c.constraints:
            last_param = c.constraints[param](param, last_param)

        return last_param



def study_as_df(study):
    """ Convert study to dataframe """
    completed = _completed_trials(study)

    modes = study.user_attrs["modes"]
    # fixed_mode = study.user_attrs["fixed_mode"]

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

def default_chain_scheduler(completed):
    """ Default function to determine when to chain runs. """

    n = len(completed)

    if n <= 6:
        return n % 2 == 0

    if n <= 15:
        return n % 5 == 0

    if n <= 50:
        return n % 10 == 0

    return False


def linear_lr_scheduler(start=0.6, end=1, interval=3):
    """ Creates a lr scheduler that will interpolate linearly from start to end over the first n iterations.

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


def create_calibration(name: str, calibrate: Union[CalibratorBase, Sequence[CalibratorBase]],
                       jar: Union[str, os.PathLike], config: Union[str, os.PathLike],
                       args: Union[str, Callable] = "", jvm_args="",
                       transform_persons: Callable = None,
                       transform_trips: Callable = None,
                       chain_runs: Union[bool, int, Callable] = False,
                       storage: optuna.storages.RDBStorage = None,
                       debug: bool = False
                       ) -> Tuple[optuna.Study, Callable]:
    """ Create or load an existing study for mode share calibration using asc values.

    This function returns the study and optimization objective as tuple. Which can be used like this:
        study.optimize(obj, 10)

    :param name: name of the study
    :param calibrate: (list) of calibrator instances
    :param jar: path to executable jar file of the scenario
    :param config: path to config file to run
    :param args: additional arguments to the executable jar, can also be a callback function
    :param jvm_args: additional jvm args
    :param transform_persons: callable to filter persons included in mode share
    :param transform_trips: callable to modify trips included in mode share
    :param chain_runs: automatically use the output plans of each run as input for the next, either True or number of iterations or callable
    :param storage: custom storage object to overwrite default sqlite backend
    :param debug: enable debug output
    :return: tuple of study and optimization objective.
    """

    # Init with 0
    if isinstance(calibrate, CalibratorBase):
        calibrate = [calibrate]

    # Set some custom arguments to prevent known errors on NFS
    if storage is None:
        storage = optuna.storages.RDBStorage(url="sqlite:///%s.db" % name,
                                             engine_kwargs={"connect_args": {"timeout": 100},
                                                            "isolation_level": "AUTOCOMMIT"})

    study = optuna.create_study(
        study_name=name,
        storage=storage,
        load_if_exists=True,
        directions=["minimize"] * sum(len(c.target) for c in calibrate),
        sampler=CalibrationSampler(calibrate)
    )

    if not path.exists("params"):
        makedirs("params")

    if not path.exists("runs"):
        makedirs("runs")

    study.set_user_attr("calib", [c.name for c in calibrate])
    for c in calibrate:
        c.init_study(study)

    def f(trial):

        params_path = path.join("params", "run%d.yaml" % trial.number)
        params = {}

        for c in calibrate:
            prefix = c.name + "_"
            c.update_config(trial, prefix, params)

        with open(params_path, "w") as f:
            yaml.dump(params, f, sort_keys=False)

        run_dir = "runs/%03d" % trial.number

        if os.path.exists(run_dir):
            shutil.rmtree(run_dir)

        completed = _completed_trials(study)

        # Call args if necessary
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

        mode_stats = analysis.calc_mode_stats(run_dir, transform_persons=transform_persons,transform_trips=transform_trips)

        trial.set_user_attr("mode_stats", mode_stats.to_dict(orient="tight"))

        res = []
        for c in calibrate:
            c.calc_stats(trial, run_dir, transform_persons, transform_trips)

            res.extend(c.error_metrics(trial))

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
