# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd

from optuna.trial import TrialState


def study_as_df(study):
    """ Convert study to dataframe """
    completed = completed_trials(study)

    # modes = study.user_attrs["modes"]
    # fixed_mode = study.user_attrs["fixed_mode"]

    data = []

    for i, trial in enumerate(completed):

        entry = {
            "trial": i,
            "start": trial.datetime_start,
            "duration": trial.duration,
        }

        for k, v in trial.user_attrs.items():
            if type(v) in (float, int):
                entry[k] = v

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


def linear_scheduler(start=0.6, end=1, interval=3):
    """ Creates a lr scheduler that will interpolate linearly from start to end over the first n iterations.

        :param start: Initial learning rate.
        :param end: Final learning rate to reach.
        :param interval: Number of runs until end rate should be reached.
    """
    if interval < 2:
        raise ValueError("N must be greater or equal 2.")

    def _fn(n, *args, **kwargs):

        if n > interval:
            return end

        return start + (n - 1) * (end - start) / interval

    return _fn


def completed_trials(study):
    completed = filter(lambda s: s.state == TrialState.COMPLETE, study.trials)
    return sorted(completed, key=lambda s: s.number)


def same_sign(x):
    x = x.to_numpy()
    return np.all(x >= 0) if x[0] >= 0 else np.all(x < 0)


def cli_oldstyle(yaml_arg="params"):
    """ Produces CLI for non matsim application scenarios  """

    def _f(jvm_args, jar, config, params_path, run_dir, trial_number, run_args):
        return "java %s -jar %s %s --config:controler.outputDirectory %s --config:controler.runId %03d --%s %s %s" % (
            jvm_args, jar, config, run_dir, trial_number, yaml_arg, params_path, run_args
        )

    return _f
