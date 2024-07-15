# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd

from scipy.special import xlogy
from sklearn.preprocessing import LabelBinarizer, LabelEncoder
from sklearn.utils import (
    assert_all_finite,
    check_array,
    check_consistent_length,
    column_or_1d,
)
from sklearn.metrics._classification import _weighted_sum

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


def linear_dist_scheduler(start_rate, end_rate, end_km):
    """ Creates a schedule for distance calibration, that will linear interpolate from 0 to given max distance in km."""

    diff = (end_rate - start_rate) / end_km

    def _fn(n, dist, *args, **kwargs):
        return min(start_rate + dist * diff, end_rate)

    return _fn


def completed_trials(study):
    """ Returns all completed trials sorted by number """
    completed = filter(lambda s: s.state == TrialState.COMPLETE, study.trials)
    return sorted(completed, key=lambda s: s.number)


def last_completed_trial(study):
    """ Returns the last completed trial """
    completed = completed_trials(study)
    if not completed:
        return None

    return completed[-1]


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


def log_loss(y_true, y_pred, *, eps="auto", normalize=True, sample_weight=None, labels=None):
    """Log loss, aka logistic loss or cross-entropy loss. Taken from scikit-learn 1.3."""
    y_pred = check_array(
        y_pred, ensure_2d=False, dtype=[np.float64, np.float32, np.float16]
    )
    if eps == "auto":
        eps = np.finfo(y_pred.dtype).eps

    check_consistent_length(y_pred, y_true, sample_weight)
    lb = LabelBinarizer()

    if labels is not None:
        lb.fit(labels)
    else:
        lb.fit(y_true)

    if len(lb.classes_) == 1:
        if labels is None:
            raise ValueError(
                "y_true contains only one label ({0}). Please "
                "provide the true labels explicitly through the "
                "labels argument.".format(lb.classes_[0])
            )
        else:
            raise ValueError(
                "The labels array needs to contain at least two "
                "labels for log_loss, "
                "got {0}.".format(lb.classes_)
            )

    transformed_labels = lb.transform(y_true)

    if transformed_labels.shape[1] == 1:
        transformed_labels = np.append(
            1 - transformed_labels, transformed_labels, axis=1
        )

    # Clipping
    y_pred = np.clip(y_pred, eps, 1 - eps)

    # If y_pred is of single dimension, assume y_true to be binary
    # and then check.
    if y_pred.ndim == 1:
        y_pred = y_pred[:, np.newaxis]
    if y_pred.shape[1] == 1:
        y_pred = np.append(1 - y_pred, y_pred, axis=1)

    # Check if dimensions are consistent.
    transformed_labels = check_array(transformed_labels)
    if len(lb.classes_) != y_pred.shape[1]:
        if labels is None:
            raise ValueError(
                "y_true and y_pred contain different number of "
                "classes {0}, {1}. Please provide the true "
                "labels explicitly through the labels argument. "
                "Classes found in "
                "y_true: {2}".format(
                    transformed_labels.shape[1], y_pred.shape[1], lb.classes_
                )
            )
        else:
            raise ValueError(
                "The number of classes in labels is different "
                "from that in y_pred. Classes found in "
                "labels: {0}".format(lb.classes_)
            )

    # Renormalize
    y_pred_sum = y_pred.sum(axis=1)
    if not np.isclose(y_pred_sum, 1, rtol=1e-15, atol=5 * eps).all():
        warnings.warn(
            (
                "The y_pred values do not sum to one. Starting from 1.5 this"
                "will result in an error."
            ),
            UserWarning,
        )
    y_pred = y_pred / y_pred_sum[:, np.newaxis]
    loss = -xlogy(transformed_labels, y_pred).sum(axis=1)

    return _weighted_sum(loss, sample_weight, normalize)