#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Contains calibration related functions """

__all__ = ["create_calibration", "study_as_df", "TerminationCondition", "constraints",
           "ASCCalibrator", "ASCDistCalibrator", "ASCGroupCalibrator", "utils"]

import glob
import os
import shutil
import subprocess
import sys
from os import path, makedirs
from time import sleep
from typing import Union, Sequence, Callable, Tuple

import optuna
import yaml

from . import utils, constraints
from .analysis import calc_mode_stats
from .base import CalibratorBase, TerminationCondition, to_float
from .calib_asc import ASCCalibrator
from .calib_asc_dist import ASCDistCalibrator
from .calib_group_asc import ASCGroupCalibrator
from .utils import study_as_df


class CalibrationSampler(optuna.samplers.BaseSampler):
    """ Run calibrators on obtained mode shares """

    def __init__(self, calibrators: Sequence[CalibratorBase]):
        self.calibrators = {}
        for c in calibrators:
            if c.name not in self.calibrators:
                self.calibrators[c.name] = c
            else:
                raise ValueError("Incompatible calibrators with same name occurred: %s (%s)" % (c.name, c))

    def infer_relative_search_space(self, study, trial):
        return {}

    def sample_relative(self, study, trial, search_space):
        # study._storage.set_trial_system_attr(trial._trial_id, "search_space", self._search_space)
        return {}

    def sample_independent(self, study, trial, param_name, param_distribution):

        prefix, _, param = param_name.partition("-")
        c: CalibratorBase = self.calibrators[prefix]

        mode = param.rpartition("-")[2] if "-" in param else param

        completed = utils.completed_trials(study)
        if len(completed) == 0:
            initial = to_float(c.sample_initial(param))
            initial = c.apply_constraints(param, mode, initial)

            return initial

        last = completed[-1]
        last_param = last.params[param_name]

        step = to_float(c.update_step(param, last, trial, completed))

        rate = 1.0
        if c.lr is not None:

            rate = c.lr(float(len(completed) + 1), param_name, step, trial, study)

            # rate of None or 0 would be invalid
            if not rate:
                rate = 1

            # numpy types need casting
            rate = to_float(rate)

        # Need to use storage directly, frozen trial does not save attributes
        study._storage.set_trial_user_attr(trial._trial_id, "%s_rate" % param_name, rate)
        study._storage.set_trial_user_attr(trial._trial_id, "%s_step" % param_name, step)

        last_param += rate * step

        # Call constraint if present
        last_param = c.apply_constraints(param, mode, last_param)

        return last_param


def create_calibration(name: str, calibrate: Union[CalibratorBase, Sequence[CalibratorBase]],
                       jar: Union[str, os.PathLike], config: Union[str, os.PathLike],
                       args: Union[str, Callable] = "", jvm_args="",
                       transform_persons: Callable = None,
                       transform_trips: Callable = None,
                       chain_runs: Union[bool, int, Callable] = False,
                       termination: TerminationCondition = None,
                       storage: optuna.storages.RDBStorage = None,
                       custom_cli: Callable = None,
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
    :param termination: termination condition for the study
    :param storage: custom storage object to overwrite default sqlite backend
    :param custom_cli: the scenario is not a matsim application and needs a different command line syntax
    :param debug: enable debug output
    :return: tuple of study and optimization objective.
    """

    # Convert to list if single instance
    if isinstance(calibrate, CalibratorBase):
        calibrate = [calibrate]

    # Set some custom arguments to prevent known errors on NFS
    if storage is None:
        storage = optuna.storages.RDBStorage(url="sqlite:///%s.db" % name,
                                             engine_kwargs={"connect_args": {"timeout": 100},
                                                            "isolation_level": "AUTOCOMMIT"})

    if not os.access(jar, os.R_OK):
        raise ValueError("Can not access JAR File: %s" % jar)

    if not os.access(config, os.R_OK):
        raise ValueError("Can not access config File: %s" % config)

    study = optuna.create_study(
        study_name=name,
        storage=storage,
        load_if_exists=True,
        directions=["minimize"] * sum(c.num_targets for c in calibrate),
        sampler=CalibrationSampler(calibrate)
    )

    if not path.exists("params"):
        makedirs("params")

    if not path.exists("runs"):
        makedirs("runs")

    study.set_user_attr("calib", [c.name for c in calibrate])

    for c in calibrate:
        c.init_study(study)
        c.set_termination(termination)

    def f(trial):

        params_path = path.join("params", "run%d.yaml" % trial.number)
        params = {}

        for c in calibrate:
            prefix = c.name + "-"
            c.update_config(study, trial, prefix, params)

        with open(params_path, "w") as f:
            yaml.dump(params, f, sort_keys=False)

        run_dir = "runs/%03d" % trial.number

        if os.path.exists(run_dir):
            shutil.rmtree(run_dir)

        completed = utils.completed_trials(study)

        # Call args if necessary
        run_args = args(completed) if callable(args) else args

        if custom_cli:
            cmd = custom_cli(jvm_args, jar, config, params_path, run_dir, trial.number, run_args)
        else:
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
                print("The scenario could not be run properly and returned with an error code.", file=sys.stderr)
                if not debug:
                    print("Set debug=True and check the output for any errors.", file=sys.stderr)
                    print("Alternatively run the cmd from the log above manually and check for errors.", file=sys.stderr)

                raise Exception("Process returned with error code: %s." % p.returncode)
        finally:
            p.terminate()

        mode_stats = calc_mode_stats(run_dir,
                                     transform_persons=transform_persons,
                                     transform_trips=transform_trips)

        trial.set_user_attr("mode_stats", mode_stats.to_dict(orient="tight"))

        err = []
        for c in calibrate:
            e = c.calc_stats(trial, run_dir, transform_persons, transform_trips)
            err.extend(to_float(f) for f in e)

        return err

    return study, f
