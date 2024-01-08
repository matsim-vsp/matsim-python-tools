# -*- coding: utf-8 -*-

import sys
from typing import Sequence, Callable, Dict

import optuna

from .base import CalibratorBase, CalibrationInput, to_float
from .analysis import calc_mode_share


class ASCCalibrator(CalibratorBase):
    """ Calibrates the alternative specific constant for desired modes """

    def __init__(self,
                 modes: Sequence[str],
                 initial: CalibrationInput,
                 target: CalibrationInput,
                 fixed_mode: str = "walk",
                 lr: Callable[[int, str, float, optuna.Trial, optuna.Study], float] = None,
                 constraints: Dict[str, Callable[[str, float], float]] = None):
        """Constructor

        :param modes: list of all relevant modes
        :param initial: dict of initial asc values
        :param target: target shares as csv or dict
        :param fixed_mode: the fixed mode with asc=0
        :param lr: learning rate schedule, will be called with (trial number, mode, update, trial, study)
        :param constraints: constraints for each mode, must return asc and will be called with original asc
        """
        super().__init__(modes, initial, target, lr, constraints)

        self.fixed_mode = fixed_mode

        self.target = self.target.rename(columns={"value": "share", "main_mode": "mode"}, errors="ignore")
        self.target = self.target.groupby("mode").agg(share=("share", "sum"))

    @property
    def name(self):
        return "asc"

    def init_study(self, study: optuna.Trial):
        study.set_user_attr("modes", self.modes)
        study.set_user_attr("fixed_mode", self.fixed_mode)

        print("Running study with target:", self.target)

    def update_config(self, study: optuna.Study, trial: optuna.Trial, prefix: str, config: dict):

        # Update constants
        for mode in self.modes:
            m = self.get_mode_params(config, mode)
            m["constant"] = trial.suggest_float(prefix + mode, sys.float_info.min, sys.float_info.max)

    def sample_initial(self, param: str) -> float:
        if param in self.initial.index:
            return self.initial.loc[param]

        return 0

    def update_step(self, param: str, last_trial: optuna.Trial, completed: Sequence[optuna.Trial]) -> float:

        if param == self.fixed_mode:
            return 0

        step = self.calc_asc_update(self.target.loc[param].share, last_trial.user_attrs["%s_share" % param],
                                    self.target.loc[self.fixed_mode].share,
                                    last_trial.user_attrs["%s_share" % self.fixed_mode])

        return step

    def calc_stats(self, trial: optuna.Trial, run_dir: str,
                   transform_persons: Callable = None,
                   transform_trips: Callable = None) -> Sequence[float]:

        shares = calc_mode_share(run_dir, transform_persons=transform_persons, transform_trips=transform_trips)
        print("Obtained mode shares:", shares)

        for k, v in shares.items():
            trial.set_user_attr("%s_share" % k, v)
            trial.set_user_attr("%s_mae" % k, to_float(abs(self.target.loc[k] - v)))

        return [to_float(abs(self.target.loc[mode] - trial.user_attrs["%s_share" % mode])) for mode in self.modes]
