# -*- coding: utf-8 -*-

import sys
import yaml
from collections import namedtuple
from typing import Sequence, Callable, Dict


import numpy as np
import optuna
import pandas as pd

from .analysis import read_trips_and_persons
from .base import CalibratorBase, CalibrationInput, LR, to_float, get_or_default, sanitize
from .group import Group, parse_group, detect_binned_groups
from .utils import last_completed_trial

# Type alias for distance learning rate schedule
# Args: runs, median_dist, mode, trial
DistLR = Callable[[int, float, str, optuna.Trial], float]

InitialState = namedtuple("InitialState", ["constant", "distGroups", "deltaPerDistGroup"])

def get_dist_params(config, subpopulation, mode):
    """ Return the distance parameters for a mode """

    if "advancedScoring" not in config:
        config["advancedScoring"] = {}

    if "scoringParameters" not in config["advancedScoring"]:
        config["advancedScoring"]["scoringParameters"] = []

    ps = config["advancedScoring"]["scoringParameters"]

    for p in ps:
        if "subpopulation" not in p:
            continue

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


def get_group_params(config, group, value, mode):
    """ Return mode params for certain subgroup """

    if "advancedScoring" not in config:
        config["advancedScoring"] = {}

    if "scoringParameters" not in config["advancedScoring"]:
        config["advancedScoring"]["scoringParameters"] = []

    ps = config["advancedScoring"]["scoringParameters"]

    for p in ps:
        if p.get(group) != value:
            continue

        if "modeParams" in p:
            for m in p["modeParams"]:
                if m["mode"] == mode:
                    return m

            m = {"mode": mode}
            p["modeParams"].append(m)
            return m

    m = {"mode": mode}
    ps.append({group: value, "modeParams": [m]})
    return m


class ASCDistCalibrator(CalibratorBase):
    """ Calibrates the alternative specific constant and marginal utility of distance for desired modes """

    def __init__(self,
                 modes: Sequence[str],
                 initial: CalibrationInput,
                 target: CalibrationInput,
                 fixed_mode: str = "walk",
                 fixed_mode_dist: str = None,
                 groups: Sequence[str] = tuple(),
                 subpopulation: str = "person",
                 lr: LR = None,
                 constraints: Dict[str, Callable[[str, float], float]] = None,
                 dist_lr: DistLR = None,
                 adjust_dist: bool = False):
        """Constructor

        :param modes: list of all relevant modes
        :param initial: dict of initial asc values
        :param target: target shares as csv or dict
        :param fixed_mode: the fixed mode with asc=0
        :param fixed_mode_dist: the fixed mode with dist_util=0
        :param groups: calibrate subgroups
        :param subpopulation: subpopulation to calibrate, this is required for the advanced scoring config
        :param lr: learning rate schedule, will be called with (trial number, mode, update, trial, study)
        :param constraints: constraints for each param, must return the value and will be called with original value
        :param dist_lr: callable, see DistLR type
        :param adjust_dist: adjust the distance distributions so that reference and obtained match
        """
        super().__init__(modes, initial, target, lr, constraints)

        if adjust_dist:
            raise NotImplementedError("Adjusting distance distributions is not implemented yet")

        self.fixed_mode = fixed_mode
        self.fixed_mode_dist = fixed_mode_dist if fixed_mode_dist else fixed_mode
        self.subpopulation = subpopulation
        self.dist_lr = dist_lr
        self.groups = groups

        for g in self.groups:
            if g not in target.columns:
                raise ValueError("Group %s not found in target" % g)

        self.target = self.target.rename(columns={"value": "share", "main_mode": "mode"}, errors="ignore")
        self.group_target = self.target

        self.dist_bins, self.dist_groups = detect_binned_groups(self.target.dist_group)

        if self.groups:
            self.base = self.get_group(self.target, None)
            self.base = self.base.groupby("mode").agg(target=("share", "sum"))

            # TODO: extra groups in file are not filtered, either remove or norm again
            # Normalize base
            self.base.target /= self.base.target.sum()

            self.target = self.get_group(self.target, None)
            self.target = self.target.groupby(["mode", "dist_group"]).agg(target=("share", "sum"))
            self.target = self.target.reset_index().set_index(["dist_group"])

            self.group_target = self.group_target.groupby(self.groups + ["mode"]).agg(
                target=("share", "sum")).reset_index()
            self.groups = [Group(g, self.group_target[g].unique()) for g in self.groups]

            # Normalize shares within each group value
            for g in self.groups:
                for v in g.values:
                    idx = self.group_target[g.name] == v
                    sub = self.group_target.loc[idx, "target"]
                    self.group_target.loc[idx, "target"] = sub / sub.sum()


        else:
            self.base = self.target.groupby("mode").agg(target=("share", "sum"))
            self.target = self.target.rename(columns={"share": "target"}, errors="ignore").set_index(["dist_group"])
            self.group_target = None

        # Normalize per distance group
        for dist_group in self.dist_groups:
            sub = self.target.loc[dist_group, "target"]
            self.target.loc[dist_group, "target"] = sub / sub.sum()

        # Target is for dist groups
        self.target = self.target.reset_index().set_index(["dist_group", "mode"])

    @property
    def name(self):
        return "asc"

    @property
    def num_targets(self):
        return len(self.base)

    @classmethod
    def read_initial(cls, arg) -> InitialState:
        """ Load previous parameters from yaml file """

        # if no yaml file is given, only asc are used initially
        if not isinstance(arg, str) or (not arg.endswith(".yaml") and not arg.endswith(".yml")):
            return InitialState(sanitize(cls.convert(arg)), None, None)

        with open(arg, "r") as f:
            data = yaml.safe_load(f)

        constants = None
        if "scoring" in data:
            # Always use first modeParams
            modeParams = data["scoring"]["scoringParameters"][0]["modeParams"]
            constants = sanitize(pd.DataFrame(modeParams)).set_index("mode")
        else:
            raise ValueError("No initial mode constants found in the yaml file")

        distGroups = None
        distParams = {}
        if "advancedScoring" in data:

            distGroups = data["advancedScoring"]["distGroups"]
            # TODO: find mode params that have subpopulation / deltaPerDistGeop
            modeParams = data["advancedScoring"]["scoringParameters"][0]["modeParams"]

            for m in modeParams:
                utils = []
                base = get_or_default(constants, m["mode"], 0)

                # The utils have been written as differences, this operation is reverted here
                for x in m["deltaPerDistGroup"]:
                    utils.append(base + x)
                    base += x

                distParams[m["mode"]] = utils

        return InitialState(constants, distGroups, distParams)

    def init_study(self, study: optuna.Trial):
        study.set_user_attr("modes", self.modes)
        study.set_user_attr("dist_groups", self.dist_groups)
        study.set_user_attr("fixed_mode", self.fixed_mode)
        study.set_user_attr("fixed_mode_dist", self.fixed_mode_dist)
        study.set_user_attr("groups", [g.name for g in self.groups])

        print("Running study with dist groups:", self.dist_groups)

        if self.groups:
            print("Calibrating groups:", self.groups)

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

            # Update dist deltas
            base = constant
            for i, dist_group in enumerate(self.dist_groups):
                param = "{%s}-%s" % (dist_group, mode)

                # returns target at median dist
                target_util = trial.suggest_float(prefix + param, sys.float_info.min, sys.float_info.max)

                # No initial state result in no dist group for first run
                if last_trial is None:
                    # TODO: not compatible wih initial logic yet
                    trial.set_user_attr("%s-%s_util" % (dist_group, mode), 0)
                    continue

                # Operate on the update steps, the actual target_util is not used here directly
                #step = self.current_step[prefix + param]

                # Constraints operate on the delta to the constant asc
                delta = self.apply_constraints(param, mode, target_util - base)

                trial.set_user_attr("%s-%s_util" % (dist_group, mode), target_util)

                # TODO: not available with new initial logic
                median_dist = last_trial.user_attrs[dist_group + "_median_dist"]

                # Store median dists
                dists.add(int(median_dist))
                utils_dist.append(delta)

                # TODO: might correct target util agsinst contrained detla
                base = target_util

            # Update group deltas
            for g in self.groups:
                # Iterate distinct values per group
                for v in g.values:
                    attr = (str(g.name) + "=" + str(v))

                    param = "[%s]-%s" % (attr, mode)
                    p = trial.suggest_float(prefix + param, sys.float_info.min, sys.float_info.max)

                    # don't write certain values
                    if p == 0 and mode == self.fixed_mode:
                        continue

                    m = get_group_params(config, g.name, v, mode)

                    step = 1 / (len(self.groups))

                    delta = (p - constant) * step
                    m["deltaConstant"] = delta
                    trial.set_user_attr("%s_delta" % param, delta)

        # write distance groups
        config["advancedScoring"]["distGroups"] = ",".join("%d" % x for x in sorted(dists))

    def sample_initial(self, param: str) -> float:
        group, _, mode = param.rpartition("-")

        if group and group.startswith("{"):
            if self.initial.deltaPerDistGroup is not None and mode in self.initial.deltaPerDistGroup:
                group = group.strip("{}")
                idx = self.dist_groups.index(group)
                return self.initial.deltaPerDistGroup[mode][idx]

            return 0

        # Grouped and base asc have the same initial value
        # TODO: support initial grouped values
        if mode in self.initial.constant.index:
            return self.initial.constant.loc[mode]

        return 0

    def update_step(self, param: str, last_trial: optuna.Trial, trial: optuna.Trial,
                    completed: Sequence[optuna.Trial]) -> float:

        if param == self.fixed_mode:
            return 0

        # Grouped asc util
        if param.startswith("["):

            p, _, mode = param.rpartition("-")
            if mode == self.fixed_mode:
                return 0

            t = self.get_group(self.group_target, parse_group(p)).set_index("mode")

            return self.calc_asc_update(t.loc[mode].target, last_trial.user_attrs["%s_share" % param],
                                        t.loc[self.fixed_mode].target,
                                        last_trial.user_attrs["%s-%s_share" % (p, self.fixed_mode)])

        # Distance util
        if param.startswith("{"):
            dist_group, _, mode = param.rpartition("-")
            dist_group = dist_group.strip("{}")

            if mode == self.fixed_mode_dist:
                return 0

            median_dist = last_trial.user_attrs[dist_group + "_median_dist"]
            lr = 1 if not self.dist_lr else self.dist_lr(len(completed) + 1, median_dist / 1000, mode, trial)

            return lr * self.calc_asc_update(self.target.loc[dist_group, mode].target,
                                             last_trial.user_attrs["%s-%s_share" % (dist_group, mode)],
                                             self.target.loc[dist_group, self.fixed_mode_dist].target,
                                             last_trial.user_attrs["%s-%s_share" % (dist_group, self.fixed_mode_dist)])

        # base asc
        return self.calc_asc_update(self.base.loc[param].target,
                                    last_trial.user_attrs["%s_share" % param],
                                    self.base.loc[self.fixed_mode].target,
                                    last_trial.user_attrs["%s_share" % self.fixed_mode])

    def calc_stats(self, trial: optuna.Trial, run_dir: str,
                   transform_persons: Callable = None,
                   transform_trips: Callable = None) -> Sequence[float]:

        trips, persons = read_trips_and_persons(run_dir,
                                                transform_persons=transform_persons,
                                                transform_trips=transform_trips)

        trips["dist_group"] = pd.cut(trips.traveled_distance, bins=self.dist_bins, labels=self.dist_groups)

        for g in self.groups:
            trips[g.name] = g.categorize(trips[g.name])

        base_share = trips.groupby("main_mode").count()["trip_number"] / len(trips)
        base_share = self.base.merge(base_share, left_index=True, right_index=True).rename(
            columns={"trip_number": "share"})

        base_share["mae"] = np.abs(base_share.share - base_share.target)

        for kv in base_share.itertuples():
            trial.set_user_attr("%s_share" % kv.Index, kv.share)
            trial.set_user_attr("%s_mae" % kv.Index, kv.mae)

        print("Obtained base shares:")
        print((base_share * 100).to_string(line_width=160, float_format=lambda x: "%.2f" % x))
        print()

        dist_err = []
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

            share.columns = pd.MultiIndex.from_product([[dist_group], share.columns])
            dist_err.append(share)

        print("Obtained dist shares:")

        df = pd.concat(dist_err, axis=1) * 100
        print(df.to_string(line_width=160, float_format=lambda x: "%.2f" % x))

        errs = []
        for g in self.groups:

            g_errs = []

            for v in g.values:

                sub_trips = self.get_group(trips, {g.name: v})
                sub_share = sub_trips.groupby("main_mode").count()["trip_number"] / len(sub_trips)
                sub_share.rename("share", inplace=True)

                if len(sub_trips) == 0:
                    print("Empty subgroup %s=%s" % (g.name, v), file=sys.stderr)

                target = self.get_group(self.group_target, {g.name: v}).rename(columns={"share": "target"})
                target = target.merge(sub_share, how="outer", left_on="mode", right_index=True)
                target.share.fillna(0, inplace=True)

                target["mae"] = np.abs(target.share - target.target)

                attr = (str(g.name) + "=" + str(v))
                for kv in target.itertuples():
                    trial.set_user_attr("[%s]-%s_share" % (attr, kv.mode), kv.share)
                    trial.set_user_attr("[%s]-%s_mae" % (attr, kv.mode), kv.mae)

                errs.append(target)

                target = target.drop(columns=[g.name]).set_index("mode")
                target.columns = pd.MultiIndex.from_product([[attr], target.columns])
                g_errs.append(target)

            df = pd.concat(g_errs, axis=1) * 100
            print("Obtained group shares for %s:" % g.name)
            print(df.to_string(line_width=160, float_format=lambda x: "%.2f" % x))

        if self.groups and errs:
            errs = pd.concat(errs)
            for g in self.groups:
                sub_err = errs.groupby(g.name).agg(sum_mae=("mae", "sum"))

                for e in sub_err.itertuples():
                    trial.set_user_attr("%s=%s_sum_mae" % (g.name, e.Index), e.sum_mae)

        return base_share.mae.to_numpy()
