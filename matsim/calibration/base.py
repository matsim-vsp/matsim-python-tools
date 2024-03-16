# -*- coding: utf-8 -*-

import math
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import reduce
from typing import Union, Sequence, Dict, Tuple, Callable

import optuna
import pandas as pd

from .constraints import F

# Type alias for input variables
CalibrationInput = Union[str, os.PathLike, dict, pd.DataFrame]

# Type alias for learning rate schedule, returns the learning rate for a given trial
LR = Callable[[int, str, float, optuna.Trial, optuna.Study], float]


def to_float(x):
    return float(x.iloc[0]) if isinstance(x, pd.Series) else float(x)


def sanitize(x):
    if 'main_mode' in x.columns and 'mode' not in x.columns:
        x.rename(columns={'main_mode': 'mode'}, inplace=True)

    return x


@dataclass
class TerminationCondition:
    """ Termination criteria for calibration. If multiple threshold are given, all must be met. """

    """ Absolute error threshold """
    abs_error: float = None

    """ Relative error threshold """
    rel_error: float = None


class CalibratorBase(ABC):
    """ Base class for calibrators.  """

    def __init__(self,
                 modes: Sequence[str],
                 initial: CalibrationInput,
                 target: CalibrationInput,
                 lr: LR = None,
                 constraints: Dict[str, F] = None):
        """Abstract constructors for all calibrations. Usually the same parameters should be made available subclasses.

        :param modes: list of all relevant modes
        :param initial: dict of initial asc values
        :param target: target shares as csv or dict
        :param lr: learning rate schedule, will be called with (trial number, mode, update, trial, study)
        :param constraints: constraints for each mode, must return a value and will be called with specific param name and original value
        """
        self.modes = modes
        self.initial = sanitize(self.convert(initial))
        self.target = sanitize(self.convert(target))
        self.lr = lr
        self.constraints = constraints
        self.terminate_cond = None
        self.terminate = False
        self.groups = []
        self.multi_groups = set()
        # Store update steps for each trial
        self.current_step = {}
        self.current_params = {}

    def set_termination(self, terminate: TerminationCondition):
        """ Set termination condition for calibration """
        self.terminate_cond = terminate

    def check_termination(self, target, observed):
        """ Check if calibration should be terminated. This will update the terminate attribute internally. """
        if self.terminate_cond is None:
            self.terminate = False

        # TODO: not used yet

        self.terminate = False

    def check_constraints(self, param, mode):
        """ Whether the default constraints should be applied, if not the implementation must do it itself."""
        return True

    def apply_constraints(self, param, mode, value):
        """ Apply constraints to a parameter. """
        if self.constraints is not None and mode in self.constraints:
            return self.constraints[mode](param, value)

        return value

    def get_group(self, df, groups: dict = None, use_multi=False):
        """ Get all row for one group"""
        # return result for empty groups
        if groups is None:
            idx = reduce(lambda x, y: x & y, [pd.isna(df[g]) for g in self.groups])
            return df[idx]

        if use_multi:
            idx = []
            for g, v in groups.items():
                if g in self.multi_groups:
                    vs = v.split(",")
                    idx.append(df[g].isin(vs))
                else:
                    idx.append(df[g] == v)

            idx = reduce(lambda x, y: x & y, idx)
        else:
            idx = reduce(lambda x, y: x & y, [df[g] == v for g, v in groups.items()])

        return df[idx]

    @property
    @abstractmethod
    def name(self):
        """ Short name of the calibrator. Will be used to differentiate attributes"""

        raise NotImplemented

    @property
    def num_targets(self):
        """ Number of targets/errors that will be returned in calc stats"""
        return len(self.target)

    @abstractmethod
    def init_study(self, study: optuna.Study):
        """ Initialize study instance  """
        raise NotImplemented

    @abstractmethod
    def update_config(self, study: optuna.Study, trial: optuna.Trial, prefix: str, config: dict):
        """ Calculate updated config for this trial. This method must interact with the trial using
         `trial.suggest_float` and by using the given prefix . """
        raise NotImplemented

    @abstractmethod
    def sample_initial(self, param: str) -> float:
        """  Sample initial value for parameter """
        raise NotImplemented

    @abstractmethod
    def update_step(self, param: str, last_trial: optuna.Trial, trial: optuna.Trial,
                    completed: Sequence[optuna.Trial]) -> float:
        """ Return update step for param based on last trial / current trial """
        raise NotImplemented

    @abstractmethod
    def calc_stats(self, trial: optuna.Trial, run_dir: str,
                   transform_persons: Callable = None,
                   transform_trips: Callable = None) -> Tuple[float]:
        """ Calculate and store statistics for a trial. These usually needs to be accessed for calculating updates.

         :return: reported error metrics
         """
        raise NotImplemented

    @classmethod
    def convert(cls, arg) -> pd.DataFrame:
        """ Method call to create target values from input argument """
        if isinstance(arg, pd.DataFrame):
            return arg
        if isinstance(arg, dict):
            # Convert simple dict of modes and values
            return pd.DataFrame(index=arg.keys(), data=arg.values(), columns=["value"]).rename_axis(index="mode")

        if arg.endswith(".csv"):
            return pd.read_csv(arg)

        return cls.convert_input(arg)

    @classmethod
    def convert_input(cls, path) -> pd.DataFrame:
        """ Convert any input file that has been passed as argument and needs to be converted. """
        raise ValueError(f"Input {path} of {type(path)} is not supported. Use csv or dataframes, or implement custom conversion method.")

    @staticmethod
    def get_mode_params(config: dict, mode: str):
        """ Retrieve the mode params from config object. Create if they don't exist yet. """
        if "scoring" not in config:
            config["scoring"] = {}

        if "scoringParameters" not in config["scoring"]:
            config["scoring"]["scoringParameters"] = []

        ps = config["scoring"]["scoringParameters"]

        for p in ps:
            if "modeParams" in p:
                for m in p["modeParams"]:
                    if m["mode"] == mode:
                        return m

                m = {"mode": mode}
                p["modeParams"].append(m)
                return m

        m = {"mode": mode}
        ps.append({"modeParams": [m]})
        return m

    @staticmethod
    def calc_asc_update(z_i, m_i, z_0, m_0) -> float:
        """ Calculates the asc update for one step """
        # Update asc
        # (1) Let z_i be the observed share of mode i. (real data, to be reproduced)
        # (2) Run the simulation to convergence. Obtain simulated mode shares m_i.
        # (3) Do nothing for mode 0. For all other modes: add [ln(z_i) - ln(m_i)] – [ln(z_0) - ln(m_0)] to its ASC.
        # (4) Goto 2.
        if m_i == 0:
            return 0

        #        return math.log((m_0 * z_i) / (m_i * z_0))
        return math.log(z_i) - math.log(m_i) - (math.log(z_0) - math.log(m_0))
