# -*- coding: utf-8 -*-

import sys
from typing import Sequence, Callable, Dict, Tuple

import numpy as np
import optuna
import pandas as pd

from .analysis import read_trips_and_persons
from .base import CalibratorBase, CalibrationInput


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

    # Same function as in preparation.py, not importeed to avoid dependency
    res = ["%.0f - %.0f" % (bins[i], bins[i + 1]) for i in range(len(bins) - 1)]
    if bins[-1] == np.inf:
        res[-1] = "%.0f+" % bins[-2]

    # Check if all groups are present
    for r in res:
        if r not in s:
            raise ValueError("Missing dist group %s" % r)

    return bins, res


def get_dist_params(config, mode):
    """ Return the distance parameters for a mode """

    if "vspScoring" not in config:
        config["vspScoring"] = {}

    if "modeParams" not in config["vspScoring"]:
        config["vspScoring"]["modeParams"] = []

    for m in config["vspScoring"]["modeParams"]:
        if m["mode"] == mode:
            return m

    m = {"mode": mode}
    config["vspScoring"]["modeParams"].append(m)
    return m


class ASCDistCalibrator(CalibratorBase):
    """ Calibrates the alternative specific constant and marginal utility of distance for desired modes """

    def __init__(self,
                 modes: Sequence[str],
                 initial: CalibrationInput,
                 target: CalibrationInput,
                 fixed_mode: str = "walk",
                 lr: Callable[[int, str, float, optuna.Trial, optuna.Study], float] = None,
                 constraints: Dict[str, Callable[[str, float], float]] = None,
                 dist_step: float = 0.5,
                 adjust_dist: bool = False):
        """Constructor

        :param modes: list of all relevant modes
        :param initial: dict of initial asc values
        :param target: target shares as csv or dict
        :param fixed_mode: the fixed mode with asc=0
        :param lr: learning rate schedule, will be called with (trial number, mode, update, trial, study)
        :param constraints: constraints for each mode, must return asc and will be called with original asc
        :param dist_step: how strong to adjust the distance parameters
        :param adjust_dist: adjust the distance distributions so that reference and obtained match
        """
        super().__init__(modes, initial, target, lr, constraints)

        self.fixed_mode = fixed_mode
        self.dist_step = dist_step

        self.target = self.target.rename(columns={"value": "share", "main_mode": "mode"}, errors="ignore")

        self.base = self.target.groupby("mode").agg(share=("share", "sum"))
        self.dist_bins, self.dist_groups = detect_dist_groups(self.target.dist_group)

        self.target = self.target.set_index(["dist_group", "mode"])

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

        print("Running study with dist groups:", self.dist_groups)
        print("Running study with target:", self.base)

    def update_config(self, study: optuna.Study, trial: optuna.Trial, prefix: str, config: dict):

        # Update constants
        for mode in self.modes:
            m = self.get_mode_params(config, mode)

            # Constant
            base = trial.suggest_float(prefix + mode, sys.float_info.min, sys.float_info.max)
            m["constant"] = base

            offset = base

            if mode == self.fixed_mode:
                continue

            dist_param = get_dist_params(config, mode)

            for i, dist_group in enumerate(self.dist_groups):
                param = "[%s]-%s" % (dist_group, mode)

                # returns target util which is converted to dist utility
                target_util = trial.suggest_float(prefix + param, sys.float_info.min, sys.float_info.max)

                delta = (target_util - base) * self.dist_step

                # TODO: finish this calculation

                dist_param[self.dist_bins[i]] = delta

        # inf group is not written
        config["vspScoring"]["distGroups"] = ",".join("%d" % x for x in self.dist_bins[:-1])

    def sample_initial(self, param: str) -> float:
        attr, _, mode = param.rpartition("-")

        if mode in self.initial.index:
            return self.initial.loc[mode]

        # TODO: Load from column with same format as input
        return 0

    def update_step(self, param: str, last_trial: optuna.Trial, completed: Sequence[optuna.Trial]) -> float:

        if param == self.fixed_mode:
            return 0

        # Base mode shares
        if not param.startswith("["):
            return self.calc_asc_update(self.base.loc[param].target, last_trial.user_attrs["%s_share" % param],
                                        self.base.loc[self.fixed_mode].target,
                                        last_trial.user_attrs["%s_share" % self.fixed_mode])

        dist_group, _, mode = param.rpartition("-")
        dist_group = dist_group.strip("[]")

        if mode == self.fixed_mode:
            return 0

        return self.calc_asc_update(self.target.loc[dist_group, mode].share,
                                    last_trial.user_attrs["%s-%s_share" % (dist_group, mode)],
                                    self.target.loc[dist_group, self.fixed_mode].share,
                                    last_trial.user_attrs["%s-%s_share" % (dist_group, self.fixed_mode)])

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

        for dist_group in self.dist_groups:
            df = trips[trips.dist_group == dist_group]

            base_share = df.groupby("main_mode").count()["trip_number"] / len(df)

            # TODO: store and evaluate dist group shares
            # store median dist

        return base_share.mae.to_numpy()
