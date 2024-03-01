# -*- coding: utf-8 -*-

import sys
from typing import Sequence, Callable, Dict, Tuple

import numpy as np
import optuna
import pandas as pd

from .analysis import read_trips_and_persons
from .base import CalibratorBase, CalibrationInput, to_float
from .utils import last_completed_trial


def detect_dist_groups(s: pd.Series) -> Tuple[Sequence, Sequence]:
    """ Detect dist bins and labels from existing groups"""
    bins = set()
    s = set(s)

    for label in s:
        if "-" in label:
            a, b = label.split("-")
            bins.add(int(a))
            bins.add(int(b))
        elif "+" in label:
            a = int(label[:-1])
            bins.add(a)
            bins.add(np.Inf)

    bins = sorted(list(bins))

    # Same function as in preparation.py, not imported to avoid dependency
    res = ["%.0f - %.0f" % (bins[i], bins[i + 1]) for i in range(len(bins) - 1)]
    if bins[-1] == np.inf:
        res[-1] = "%.0f+" % bins[-2]

    # Check if all groups are present
    for r in res:
        if r not in s:
            raise ValueError("Missing dist group %s" % r)

    return bins, res


def get_dist_params(config, subpopulation, mode):
    """ Return the distance parameters for a mode """

    if "advancedScoring" not in config:
        config["advancedScoring"] = {}

    if "scoringParameters" not in config["advancedScoring"]:
        config["advancedScoring"]["scoringParameters"] = []

    ps = config["advancedScoring"]["scoringParameters"]

    for p in ps:
        if "modeParams" in p:
            for m in p["modeParams"]:
                if m["mode"] == mode:
                    return m

            m = {"mode": mode, "deltaPerDistGroup": []}
            p["modeParams"].append(m)
            return m

    m = {"mode": mode, "deltaPerDistGroup": []}
    ps.append({"subpopulation": subpopulation, "modeParams": [m]})
    return m


class ASCDistCalibrator(CalibratorBase):
    """ Calibrates the alternative specific constant and marginal utility of distance for desired modes """

    def __init__(self,
                 modes: Sequence[str],
                 initial: CalibrationInput,
                 target: CalibrationInput,
                 fixed_mode: str = "walk",
                 fixed_mode_dist: str = None,
                 subpopulation: str = "person",
                 lr: Callable[[int, str, float, optuna.Trial, optuna.Study], float] = None,
                 constraints: Dict[str, Callable[[str, float], float]] = None,
                 dist_update_weight: float = 1,
                 adjust_dist: bool = False):
        """Constructor

        :param modes: list of all relevant modes
        :param initial: dict of initial asc values
        :param target: target shares as csv or dict
        :param fixed_mode: the fixed mode with asc=0
        :param fixed_mode_dist: the fixed mode with dist_util=0
        :param subpopulation: subpopulation to calibrate, this is required for the advanced scoring config
        :param lr: learning rate schedule, will be called with (trial number, mode, update, trial, study)
        :param constraints: constraints for each param, must return the value and will be called with original value
        :param dist_update_weight: how strong to adjust the distance parameters in relation to asc
        :param adjust_dist: adjust the distance distributions so that reference and obtained match
        """
        super().__init__(modes, initial, target, lr, constraints)

        if adjust_dist:
            raise NotImplementedError("Adjusting distance distributions is not implemented yet")

        self.fixed_mode = fixed_mode
        self.fixed_mode_dist = fixed_mode_dist if fixed_mode_dist else fixed_mode
        self.subpopulation = subpopulation
        self.dist_update_weight = dist_update_weight

        self.target = self.target.rename(columns={"value": "share", "main_mode": "mode"}, errors="ignore")

        self.base = self.target.groupby("mode").agg(target=("share", "sum"))

        self.dist_bins, self.dist_groups = detect_dist_groups(self.target.dist_group)

        self.target = self.target.rename(columns={"share": "target"}, errors="ignore").set_index(["dist_group"])

        # Normalize per distance group
        for dist_group in self.dist_groups:
            sub = self.target.loc[dist_group, "target"]
            self.target.loc[dist_group, "target"] = sub / sub.sum()

        self.target = self.target.reset_index().set_index(["dist_group", "mode"])

    @property
    def name(self):
        return "asc"

    @property
    def num_targets(self):
        return len(self.base)

    def init_study(self, study: optuna.Trial):
        study.set_user_attr("modes", self.modes)
        study.set_user_attr("dist_groups", self.dist_groups)
        study.set_user_attr("fixed_mode", self.fixed_mode)
        study.set_user_attr("fixed_mode_dist", self.fixed_mode_dist)

        print("Running study with dist groups:", self.dist_groups)
        print("Running study with target:", self.base)

    def check_constraints(self, param, mode):
        # only return true for the asc constants, not the dist!
        # the dist constraints are handled separatly
        return mode == param

    def update_config(self, study: optuna.Study, trial: optuna.Trial, prefix: str, config: dict):

        dists = set()

        # Update constants
        for mode in self.modes:
            m = self.get_mode_params(config, mode)

            # Constant
            constant = trial.suggest_float(prefix + mode, sys.float_info.min, sys.float_info.max)
            m["constant"] = constant

            last_trial = last_completed_trial(study)

            if mode == self.fixed_mode_dist:
                continue

            utils_dist = get_dist_params(config, self.subpopulation, mode)["deltaPerDistGroup"]

            base = self.current_step.get(prefix + mode, 0)
            for i, dist_group in enumerate(self.dist_groups):
                param = "[%s]-%s" % (dist_group, mode)

                dist = self.dist_bins[i]

                # returns target at median dist
                target_util = trial.suggest_float(prefix + param, sys.float_info.min, sys.float_info.max)

                if last_trial is None:
                    trial.set_user_attr("%s-%s_util" % (dist_group, mode), 0)
                    continue

                # Operate on the update steps, the actual target_util is not used here directly
                step = self.current_step[prefix + param]

                # Constraints operate on the delta to the constant asc
                delta = self.apply_constraints(param, mode, step - base)

                trial.set_user_attr("%s-%s_util" % (dist_group, mode), target_util)

                median_dist = last_trial.user_attrs[dist_group + "_median_dist"]

                # Store median dists
                dists.add(int(median_dist))
                utils_dist.append(delta)

                base = step

        # write distance groups
        config["advancedScoring"]["distGroups"] = ",".join("%d" % x for x in sorted(dists))

    def sample_initial(self, param: str) -> float:
        group, _, mode = param.rpartition("-")

        # Initial value for grouped asc
        # TODO: load these as well
        if group:
            return 0

        if mode in self.initial.index:
            return self.initial.loc[mode]

        return 0

    def update_step(self, param: str, last_trial: optuna.Trial, trial: optuna.Trial,
                    completed: Sequence[optuna.Trial]) -> float:

        if param == self.fixed_mode:
            return 0

        # Both update steps sum to 1
        update_step = 1 + self.dist_update_weight

        # Base mode shares
        if not param.startswith("["):
            return (1 / update_step) * self.calc_asc_update(self.base.loc[param].target,
                                                            last_trial.user_attrs["%s_share" % param],
                                                            self.base.loc[self.fixed_mode].target,
                                                            last_trial.user_attrs["%s_share" % self.fixed_mode])

        dist_group, _, mode = param.rpartition("-")
        dist_group = dist_group.strip("[]")

        if mode == self.fixed_mode_dist:
            return 0

        # TODO: already substract from the prev util here
        # -> probably not but handle constraints up stream

        # Offset the corrections in other groups
        return (self.dist_update_weight / update_step) * self.calc_asc_update(self.target.loc[dist_group, mode].target,
                                                                              last_trial.user_attrs[ "%s-%s_share" % (dist_group, mode)],
                                                                              self.target.loc[dist_group, self.fixed_mode_dist].target,
                                                                              last_trial.user_attrs["%s-%s_share" % (dist_group, self.fixed_mode_dist)])

    def calc_stats(self, trial: optuna.Trial, run_dir: str,
                   transform_persons: Callable = None,
                   transform_trips: Callable = None) -> Sequence[float]:

        trips, persons = read_trips_and_persons(run_dir,
                                                transform_persons=transform_persons,
                                                transform_trips=transform_trips)

        trips["dist_group"] = pd.cut(trips.traveled_distance, bins=self.dist_bins, labels=self.dist_groups)

        base_share = trips.groupby("main_mode").count()["trip_number"] / len(trips)
        base_share = self.base.merge(base_share, left_index=True, right_index=True).rename(
            columns={"trip_number": "share"})

        base_share["mae"] = np.abs(base_share.share - base_share.target)

        for kv in base_share.itertuples():
            trial.set_user_attr("%s_share" % kv.Index, kv.share)
            trial.set_user_attr("%s_mae" % kv.Index, kv.mae)

        print("Obtained base shares:")
        print(base_share)
        print()

        for dist_group in self.dist_groups:
            df = trips[trips.dist_group == dist_group]

            share = df.groupby("main_mode").count()["trip_number"] / len(df)
            share = self.target.loc[dist_group, :].merge(share, left_index=True, right_index=True, how="left").rename(
                columns={"trip_number": "share"})

            # Fill zero values, if this happens calibration will probably break
            share["share"] = share["share"].fillna(0)

            share["mae"] = np.abs(share.share - share.target)

            for kv in share.itertuples():
                trial.set_user_attr("%s-%s_share" % (dist_group, kv.Index), kv.share)
                trial.set_user_attr("%s-%s_mae" % (dist_group, kv.Index), kv.mae)

            trial.set_user_attr("%s_median_dist" % dist_group, to_float(df.traveled_distance.median()))
            trial.set_user_attr("%s_sum_mae" % dist_group, to_float(share.mae.sum()))

            print("Obtained shares for dist group %s:" % dist_group)
            print(share)

        return base_share.mae.to_numpy()
