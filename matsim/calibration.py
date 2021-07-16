
import os
import subprocess
import glob
import math
import shutil
from os import path, makedirs
from time import sleep

from typing import Any, Sequence, Dict, Callable, Tuple

import yaml
import numpy as np
import pandas as pd
import geopandas
import optuna

from optuna.trial import TrialState

class ASCSampler(optuna.samplers.BaseSampler):
    """ Sample asc according to obtained mode shares """

    def __init__(self, mode_share, fixed_mode, initial_asc):

        self.mode_share = mode_share
        self.fixed_mode = fixed_mode
        self.initial_asc = initial_asc

    def infer_relative_search_space(self, study, trial):
        return {}

    def sample_relative(self, study, trial, search_space):
        #study._storage.set_trial_system_attr(trial._trial_id, "search_space", self._search_space)
        return {}

    def sample_independent(self, study, trial, param_name, param_distribution):

        if param_name == self.fixed_mode:
            return 0

        completed = filter(lambda s: s.state == TrialState.COMPLETE, study.trials)
        completed = sorted(completed, key=lambda s: s.number)

        if len(completed) == 0:
            return self.initial_asc[param_name]

        last = completed[-1]

        asc = last.params[param_name]

        asc += self.calc_update(self.mode_share[param_name], last.user_attrs["%s_share" % param_name],
                                self.mode_share[self.fixed_mode], last.user_attrs["%s_share" % self.fixed_mode])

        return asc

    def calc_update(self, z_i, m_i, z_0, m_0):
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




def calc_mode_share(run, person_filter=None, map_trips=None):
    
    trips = glob.glob(run.rstrip("/") + "/*.output_trips.csv.gz")[0]

    persons = glob.glob(run.rstrip("/") + "/*.output_persons.csv.gz")[0]

    df = pd.read_csv(trips, sep=";")
    dfp = pd.read_csv(persons, sep=";", index_col=0)

    gdf = geopandas.GeoDataFrame(dfp, 
            geometry=geopandas.points_from_xy(dfp.first_act_x, dfp.first_act_y)
    )

    if person_filter is not None:
        gdf = person_filter(gdf)

    df = df.join(gdf, on="person", how="inner")

    nans = df.main_mode.isnull()

    # use longest distance mode if there is no main mode
    df.loc[nans, "main_mode"] = df.loc[nans, "longest_distance_mode"]

    if map_trips is not None:
        df = map_trips(df)

    return df.groupby("main_mode").count()["trip_number"] / len(df)


def create_mode_share_study(name: str, jar: str, config: str,
                            modes: Sequence[str], mode_share: Dict[str, float],
                            fixed_mode: str = "walk",
                            args="", jvm_args="",
                            initial_asc: Dict[str, float] = None,
                            person_filter: Callable = None,
                            map_trips: Callable = None) -> Tuple[optuna.Study, Callable]:
    """ Create or loads an existing study for mode share calibration using asc values.

    This function returns the study and optimization objective as tuple. Which can be used like this:
        study.optimize(obj, 10)

    :param name: name of the study
    :param jar: path to executable jar file of the scenario
    :param config: path to config file to run
    :param modes: list of all relevant modes
    :param mode_share: dict of target mode shares
    :param fixed_mode: the fixed mode with asc=0
    :param args: additional arguments to the executable jar
    :param jvm_args: additional jvm args
    :param initial_asc: dict of initial asc values
    :param person_filter: callable to filter person included in mode share
    :param map_trips: callable to modify trips included in mode share
    :return: tuple of study and optimization objective.
    """

    # Init with 0
    if initial_asc is None:
        initial_asc = {}
        for m in modes:
            initial_asc[m] = 0

    study = optuna.create_study(
            study_name=name, 
            storage="sqlite:///%s.db" % name, 
            load_if_exists=True,
            directions=["minimize"] * len(modes),
            sampler=ASCSampler(mode_share, fixed_mode, initial_asc)
        )

    study.set_user_attr("modes", modes)
    study.set_user_attr("fixed_mode", fixed_mode)

    if not path.exists("params"):
        makedirs("params")

    if not path.exists("runs"):
        makedirs("runs")

    def f(trial):

        params_path = path.join("params", "run%d.yaml" % trial.number)
        params = []

        for mode in modes:
            # preserve order
            m = {"mode": mode}

            asc = trial.suggest_float(mode, -2, 2)
            m["constant"] = asc
            params.append(m)

        with open(params_path, "w") as f:
            yaml.dump({"planCalcScore": {"scoringParameters": [{"modeParams": params}]}}, f, sort_keys=False)

        run_dir = "runs/%03d" % trial.number

        if os.path.exists(run_dir):
            shutil.rmtree(run_dir)

        cmd = "java %s -jar %s run --config %s --yaml %s --output %s --runId %03d %s" \
              % (jvm_args, jar, config, params_path, run_dir, trial.number, args)

        # Extra whitespaces will brake argument parsing
        cmd = cmd.strip()

        print("Running cmd %s" % cmd)

        if os.name != 'nt':
            cmd = cmd.split(" ")

        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:    
            while p.poll() is None:
                sleep(1)

            if p.returncode != 0:
                raise Exception("Process returned with error code: %s" % p.returncode)
        finally:
            p.terminate()

        shares = calc_mode_share(run_dir, person_filter=person_filter, map_trips=map_trips)
        for k, v in shares.items():
            trial.set_user_attr("%s_share" % k, v)

        res = []
        for mode in modes:
            res.append(abs(mode_share[mode] - trial.user_attrs["%s_share" % mode]))

        return res

    return study, f