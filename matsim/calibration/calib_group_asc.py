# -*- coding: utf-8 -*-

import sys
from typing import Sequence, Callable, Dict, Literal
from functools import reduce

import numpy as np
import optuna
import pandas as pd

from .base import CalibratorBase, CalibrationInput
from .analysis import read_trips_and_persons


def get_sbb_params(config, group, value, mode):
    """ Return parameter set for specific group """

    if "SBBBehaviorGroups" not in config:
        config["SBBBehaviorGroups"] = {}

    if "behaviorGroup" not in config["SBBBehaviorGroups"]:
        config["SBBBehaviorGroups"]["behaviorGroup"] = []

    groups = config["SBBBehaviorGroups"]["behaviorGroup"]

    for b_group in groups:

        if b_group["personAttribute"] == group:

            for v in b_group["personGroupAttributeValues"]:
                if v["attributeValues"] == value:

                    for m in v["absoluteModeCorrections"]:
                        if m == mode:
                            return m

                    m = {"mode": mode}
                    v["absoluteModeCorrections"].append(m)
                    return m

            m = {"mode": mode}
            b_group["personGroupAttributeValues"].append(
                {"attributeValues": value, "absoluteModeCorrections": [m]}
            )
            return m

    m = {"mode": mode}
    groups.append({"personAttribute": group,
                   "personGroupAttributeValues":
                       [{"attributeValues": value, "absoluteModeCorrections": [m]}]})
    return m


class ASCGroupCalibrator(CalibratorBase):
    """ Calibrates the alternative specific for specific subpopulations """

    def __init__(self,
                 modes: Sequence[str],
                 initial: CalibrationInput,
                 target: CalibrationInput,
                 fixed_mode: str = "walk",
                 lr: Callable[[int, str, float, optuna.Trial, optuna.Study], float] = None,
                 constraints: Dict[str, Callable[[str, float], float]] = None,
                 config_format: Literal['default', 'sbb'] = "default"):
        """Abstract constructors for all calibrations. Usually the same parameters should be made available subclasses.

        :param modes: list of all relevant modes
        :param initial: dict of initial asc values
        :param target: target shares as csv or dict
        :param fixed_mode: the fixed mode with asc=0
        :param lr: learning rate schedule, will be called with (trial number, mode, update, trial, study)
        :param constraints: constraints for each mode, must return asc and will be called with original asc
        :param config_format: use SBBBehaviorGroups for the parameter config
        """
        super().__init__(modes, initial, target, lr, constraints)

        self.fixed_mode = fixed_mode
        self.config_format = config_format

        if "mode" not in self.target.columns:
            raise ValueError("Target must have 'mode' or 'main_mode' column")

        self.target = self.target.rename(columns={"value": "share"}, errors="ignore")

        if "mode" not in self.target.columns:
            raise ValueError("Target must have 'share' column")

        self.groups = [t for t in self.target.columns if t not in ('mode', 'share', 'asc')]

        self.base = self.get_group(self.target, None)
        self.base = self.base.groupby("mode").agg(share=("share", "sum"))

        if len(self.base) == 0:
            raise ValueError("Target must contain base without any attributes")

    def get_group(self, df, groups: dict = None):
        """ Get data of one group"""
        # return result for empty groups
        if groups is None:
            idx = reduce(lambda x, y: x & y, [pd.isna(df[g]) for g in self.groups])
            return df[idx]

    @property
    def name(self):
        return "asc"

    def init_study(self, study: optuna.Trial):
        study.set_user_attr("modes", self.modes)
        study.set_user_attr("groups", self.groups)
        study.set_user_attr("fixed_mode", self.fixed_mode)

        print("Calibrating groups:", self.groups)
        print("Running with base target:", self.base)

    def update_config(self, trial: optuna.Trial, prefix: str, config: dict):

        # Base ascs for each mode
        base = {}

        for mode in self.modes:
            m = self.get_mode_params(config, mode)
            m["constant"] = trial.suggest_float(prefix + mode, sys.float_info.min, sys.float_info.max)
            base[mode] = m["constant"]

        for g in self.groups:
            for v in set(self.target[g]):
                if pd.isna(v):
                    continue

                attr = (str(g) + "=" + str(v))
                for mode in self.modes:
                    # TODO: build config correctly
                    # Update constants
                    if self.config_format == "sbb":
                        p = trial.suggest_float(prefix + "[%s]-%s" % (attr, mode),
                                            sys.float_info.min, sys.float_info.max)

                        # don't write certain values
                        if p == 0 and mode == self.fixed_mode:
                            continue

                        m = get_sbb_params(config, g, v, mode)
                        m["deltaConstant"] = p

                    else:
                        raise ValueError("Currently only ssb config format is supported")

    def sample_initial(self, param: str) -> float:
        attr, _, mode = param.rpartition("-")

        if mode in self.initial.index and attr == "":
            return self.initial.loc[mode]

        # TODO: Load from column with same format as input

        return 0

    def update_step(self, param: str, last_trial: optuna.Trial) -> float:

        if param == self.fixed_mode:
            return 0

        step = self.calc_asc_update(self.target.loc[param].share, last_trial.user_attrs["%s_share" % param],
                                    self.target.loc[self.fixed_mode].share,
                                    last_trial.user_attrs["%s_share" % self.fixed_mode])

        return step

    def calc_stats(self, trial: optuna.Trial, run_dir: str,
                   transform_persons: Callable = None,
                   transform_trips: Callable = None) -> Sequence[float]:

        trips, persons = read_trips_and_persons(run_dir,
                                                transform_persons=transform_persons,
                                                transform_trips=transform_trips)

        errs = []

        print("TODO")

        return [(abs(self.target.loc[mode] - trial.user_attrs["%s_share" % mode])) for mode in self.modes]
