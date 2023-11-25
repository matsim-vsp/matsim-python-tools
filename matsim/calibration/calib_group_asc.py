# -*- coding: utf-8 -*-

import sys
from typing import Sequence, Callable, Dict, Literal
from functools import reduce
from collections import defaultdict

import numpy as np
import optuna
import pandas as pd

from .base import CalibratorBase, CalibrationInput
from .analysis import read_trips_and_persons
from .utils import completed_trials


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


def parse_group(p):
    p = p.strip("[]")
    return {x.split("=")[0]: x.split("=")[1] for x in p.split(",")}


class ASCGroupCalibrator(CalibratorBase):
    """ Calibrates the alternative specific for specific subpopulations """

    def __init__(self,
                 modes: Sequence[str],
                 initial: CalibrationInput,
                 target: CalibrationInput,
                 fixed_mode: str = "walk",
                 lr: Callable[[int, str, float, optuna.Trial, optuna.Study], float] = None,
                 constraints: Dict[str, Callable[[str, float], float]] = None,
                 calib_base: Literal['always', 'alternating', 'never'] = "always",
                 multi_groups: Sequence[str] = None,
                 corr_correction: float = 1,
                 config_format: Literal['default', 'sbb'] = "default"):
        """Abstract constructors for all calibrations. Usually the same parameters should be made available subclasses.

        :param modes: list of all relevant modes
        :param initial: dict of initial asc values
        :param target: target shares as csv or dict
        :param fixed_mode: the fixed mode with asc=0
        :param lr: learning rate schedule, will be called with (trial number, mode, update, trial, study)
        :param constraints: constraints for each mode, must return asc and will be called with original asc
        :param calib_base: how to calibrate the ungrouped base ASC, can be always, alternating (every 2nd iteration) or never
        :param multi_groups: Groups that contain multiple values, that will be split by ","
        :param corr_correction: factor to reduce learning rates for possibly correlated groups, 0 disables this correction
        :param config_format: use SBBBehaviorGroups for the parameter config
        """
        super().__init__(modes, initial, target, lr, constraints)

        self.fixed_mode = fixed_mode
        self.multi_groups = multi_groups
        self.corr_correction = corr_correction
        self.config_format = config_format

        if "mode" not in self.target.columns and "main_mode" not in self.target.columns:
            raise ValueError("Target must have 'mode' or 'main_mode' column")

        if calib_base not in ("always", "alternating", "never"):
            raise ValueError("calib_base must be one of 'always', 'alternating' or 'never'")

        if config_format not in ("default", "sbb"):
            raise ValueError("config_format must be one of 'default' or 'sbb'")

        self.target = self.target.rename(columns={"value": "share", "main_mode": "mode"}, errors="ignore")

        if "share" not in self.target.columns:
            raise ValueError("Target must have 'share' column")

        self.groups = [t for t in self.target.columns if t not in ('mode', 'share', 'asc')]

        if calib_base != "never":
            self.base = self.get_group(self.target, None)
            self.base = self.base.groupby("mode").agg(target=("share", "sum"))
            self.alternate_base = calib_base == "alternating"

            if len(self.base) == 0:
                raise ValueError("Target must contain base without any attributes")
        else:
            self.base = None
            self.alternate_base = False

    def get_group(self, df, groups: dict = None):
        """ Get data of one group"""
        # return result for empty groups
        if groups is None:
            idx = reduce(lambda x, y: x & y, [pd.isna(df[g]) for g in self.groups])
            return df[idx]

        idx = reduce(lambda x, y: x & y, [df[g] == v for g, v in groups.items()])
        return df[idx]

    @property
    def name(self):
        return "asc"

    @property
    def num_targets(self):
        return len(self.base)

    def init_study(self, study: optuna.Trial):
        study.set_user_attr("modes", self.modes)
        study.set_user_attr("groups", self.groups)
        study.set_user_attr("fixed_mode", self.fixed_mode)

        print("Calibrating groups:", self.groups)
        print("Running with base target:", self.base)

    def update_config(self, study: optuna.Study, trial: optuna.Trial, prefix: str, config: dict):

        # Base ascs for each mode
        base = defaultdict(lambda: 0)

        completed = completed_trials(study)

        if self.base is not None:

            if not self.alternate_base or len(completed) % 2 == 0:
                for mode in self.modes:
                    m = self.get_mode_params(config, mode)
                    m["constant"] = trial.suggest_float(prefix + mode, sys.float_info.min, sys.float_info.max)
                    base[mode] = m["constant"]
            else:
                # Use attribute from last trial
                last_trial = completed[-1]
                for mode in self.modes:
                    m = self.get_mode_params(config, mode)
                    m["constant"] = last_trial.params[prefix + mode]
                    base[mode] = m["constant"]

        step = 1
        # If all groups were fully correlated, update step needs to be divided by number of groups
        if self.corr_correction > 0:
            step = 1 / (len(self.groups) * self.corr_correction)

        # Grouped ascs
        for g in self.groups:
            for v in set(self.target[g]):
                if pd.isna(v):
                    continue

                attr = (str(g) + "=" + str(v))
                for mode in self.modes:
                    # Update constants
                    if self.config_format == "sbb":
                        param = "[%s]-%s" % (attr, mode)

                        if not self.alternate_base or len(completed) == 0 or len(completed) % 2 == 1:
                            p = trial.suggest_float(prefix + param, sys.float_info.min, sys.float_info.max)
                        else:
                            # Use from previous iteration
                            last_trial = completed[-1]
                            p = last_trial.params[prefix + mode]

                        # don't write certain values
                        if p == 0 and mode == self.fixed_mode:
                            continue

                        m = get_sbb_params(config, g, v, mode)

                        delta = (p - base[mode]) * step
                        m["deltaConstant"] = delta
                        trial.set_user_attr("%s_delta" % param, delta)
                    else:
                        raise ValueError("Currently only ssb config format is supported")

    def sample_initial(self, param: str) -> float:
        attr, _, mode = param.rpartition("-")

        if mode in self.initial.index:
            return self.initial.loc[mode]

        # TODO: Load from column with same format as input

        return 0

    def update_step(self, param: str, last_trial: optuna.Trial) -> float:

        if param == self.fixed_mode:
            return 0

        # Base mode shares
        if not param.startswith("["):
            return self.calc_asc_update(self.base.loc[param].target, last_trial.user_attrs["%s_share" % param],
                                        self.base.loc[self.fixed_mode].target,
                                        last_trial.user_attrs["%s_share" % self.fixed_mode])

        else:
            p, _, mode = param.rpartition("-")

            if mode == self.fixed_mode:
                return 0

            t = self.get_group(self.target, parse_group(p)).set_index("mode")

            # TODO: the previous applied correction might be considered here as well

            return self.calc_asc_update(t.loc[mode].share, last_trial.user_attrs["%s_share" % param],
                                        t.loc[self.fixed_mode].share,
                                        last_trial.user_attrs["%s-%s_share" % (p, self.fixed_mode)])

    def calc_stats(self, trial: optuna.Trial, run_dir: str,
                   transform_persons: Callable = None,
                   transform_trips: Callable = None) -> Sequence[float]:

        trips, persons = read_trips_and_persons(run_dir,
                                                transform_persons=transform_persons,
                                                transform_trips=transform_trips)

        if self.base is not None:
            base_share = trips.groupby("main_mode").count()["trip_number"] / len(trips)
            base_share = self.base.merge(base_share, left_index=True, right_index=True).rename(
                columns={"trip_number": "share"})

            base_share["mae"] = np.abs(base_share.share - base_share.target)

            for kv in base_share.itertuples():
                trial.set_user_attr("%s_share" % kv.Index, kv.share)
                trial.set_user_attr("%s_mae" % kv.Index, kv.mae)

            print("Obtained base shares:")
            print(base_share)

        errs = []

        for g in self.groups:
            for v in set(self.target[g]):
                if pd.isna(v):
                    continue

                sub_trips = self.get_group(trips, {g: v})
                sub_share = sub_trips.groupby("main_mode").count()["trip_number"] / len(sub_trips)
                sub_share.rename("share", inplace=True)

                if len(sub_trips) == 0:
                    print("Empty subgroup %s=%s" % (g, v), file=sys.stderr)

                target = self.get_group(self.target, {g: v}).rename(columns={"share": "target"})
                target = target.merge(sub_share, how="outer", left_on="mode", right_index=True)
                target.share.fillna(0, inplace=True)

                target["mae"] = np.abs(target.share - target.target)

                attr = (str(g) + "=" + str(v))
                for kv in target.itertuples():
                    trial.set_user_attr("[%s]-%s_share" % (attr, kv.mode), kv.share)
                    trial.set_user_attr("[%s]-%s_mae" % (attr, kv.mode), kv.mae)

                errs.append(target)

        errs = pd.concat(errs)
        print("Grouped sum of errors:")
        for g in self.groups:
            sub_err = errs.groupby(g).agg(sum_mae=("mae", "sum"))
            print(sub_err)

            for e in sub_err.itertuples():
                trial.set_user_attr("%s=%s_sum_mae" % (g, e.Index), e.sum_mae)

        return base_share.mae.to_numpy()
