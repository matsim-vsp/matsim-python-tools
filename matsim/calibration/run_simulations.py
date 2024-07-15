#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import subprocess
import sys
from os import makedirs
from time import sleep
from typing import Union, Callable

import numpy as np
import pandas as pd

METADATA = "run-simulations", "Utility to run multiple simulations at once."

def likelihood_ratio(ll, ll_null):
    return (2 * (ll - ll_null))


def likelihood_ratio_test(ll, ll_null, dof=1):
    from scipy.stats.distributions import chi2
    return chi2.sf(likelihood_ratio(ll, ll_null), dof)


def sample_y_null(shares: np.array, num_persons: int, num_samples: int):
    """ Replicates a discrete sampling of the null model. For each person, the same number of modes are drawn from the original distribution.
    This is done to make the discrete sampling of the simulation comparable to the continous probabilities of the given mode shares.
    """
    rng = np.random.default_rng(seed=4711)

    samples = rng.choice(len(shares), (num_persons, num_samples), p=shares)
    y_null = np.zeros((num_persons, len(shares)))

    for i, s in enumerate(samples):
        for j in range(len(shares)):
            c = np.sum(s == j)
            y_null[i, j] = c / num_samples

    return y_null


def process_results(runs):
    """Process results of multiple simulations"""
    from .utils import log_loss
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import LabelEncoder

    print("Processing results in %s" % runs)

    dfs = None
    for run in os.listdir(runs):
        if not os.path.isdir(os.path.join(runs, run)):
            continue

        out_path = os.path.join(runs, run, "analysis", "population", "mode_choices.csv")
        if not os.path.exists(out_path):
            print("Skipping %s, no mode_choices.csv found. Run probably not finished yet." % run)
            continue

        df = pd.read_csv(out_path)
        if dfs is None:
            dfs = df
        else:
            dfs = dfs.merge(df, left_on=["person", "n", "true_mode"], right_on=["person", "n", "true_mode"],
                            suffixes=("", "_%s" % run))

    shares = dfs.groupby("true_mode").size() / len(dfs)
    modes = shares.index

    labels = LabelEncoder().fit(modes)
    y_true = labels.transform(dfs["true_mode"])

    dists = dfs.euclidean_distance.to_numpy() / 1000
    pred_cols = [c for c in dfs.columns if c.startswith("pred_mode")]

    y_pred = np.zeros((len(y_true), len(modes)))
    y_null = sample_y_null(shares.to_numpy(), len(dfs), len(pred_cols))

    for p in dfs[pred_cols].itertuples():

        for j, m in enumerate(modes):
            c = 0
            for col in pred_cols:
                if getattr(p, col) == m:
                    c += 1

            y_pred[p.Index, j] = c / len(pred_cols)

    choices = pd.DataFrame(data=y_pred, columns=modes)
    choices.insert(0, "person", dfs.person)
    choices.insert(1, "n", dfs.n)
    choices.insert(2, "true_mode", dfs.true_mode)

    choices.to_csv(os.path.join(runs, "choices.csv"), index=False)

    accs = [accuracy_score(dfs.true_mode, dfs[col], sample_weight=dfs.weight) for col in pred_cols]
    accs_d = [accuracy_score(dfs.true_mode, dfs[col], sample_weight=dfs.weight * dists) for col in pred_cols]

    # Compute likelihood with eps as 0.01%
    eps = 0.0001

    result = [
        ("Log likelihood", -log_loss(y_true, y_pred, sample_weight=dfs.weight, eps=eps, normalize=False),
         -log_loss(y_true, y_pred, sample_weight=dfs.weight * dists, eps=eps, normalize=False)),
        ("Log likelihood (normalized)", -log_loss(y_true, y_pred, sample_weight=dfs.weight, eps=eps, normalize=True),
         -log_loss(y_true, y_pred, sample_weight=dfs.weight * dists, eps=eps, normalize=True)),
        ("Log likelihood (null)", -log_loss(y_true, y_null, sample_weight=dfs.weight, eps=eps, normalize=False),
         -log_loss(y_true, y_null, sample_weight=dfs.weight * dists, eps=eps, normalize=False)),
        ("Mean Accuracy", np.mean(accs), np.mean(accs_d)),
        ("Samples", len(dfs), sum(dists)),
        ("Runs", len(pred_cols), len(pred_cols))
    ]

    result.insert(4, ("McFadden R2", 1 - (result[0][1] / result[2][1]), 1 - (result[0][2] / result[2][2])))
    result.insert(5, ("LL ratio", likelihood_ratio(result[0][1], result[2][1]),
                      likelihood_ratio(result[0][2], result[2][2])))
    result.insert(6, ("LL ratio test (dof=1)", likelihood_ratio_test(result[0][1], result[2][1]),
                      likelihood_ratio_test(result[0][2], result[2][2])))

    df = pd.DataFrame(result, columns=["Metric", "Value", "Distance weighted"]).set_index("Metric")
    print(df)

    df.to_csv(os.path.join(runs, "results.csv"), index=True)


def run(jar: Union[str, os.PathLike],
        config: Union[str, os.PathLike],
        args: Union[str, Callable] = "",
        jvm_args="",
        runs: int = 10,
        worker_id: int = 0,
        workers: int = 1,
        seed: int = 4711,
        overwrite: bool = False,
        custom_cli: Callable = None,
        debug: bool = False):
    """Run multiple simulations using different seeds at once. Simulations will be performed sequentially.
    For parallel execution, multiple workers must be started. 

    :param jar: path to executable jar file of the scenario
    :param config: path to config file to run
    :param args: arguments to pass to the simulation
    :param jvm_args: arguments to pass to the JVM
    :param runs: number of simulations to run
    :param worker_id: id of this process
    :param workers: total number of processes
    :param seed: starting seed
    :param overwrite: overwrite existing output directory
    :param custom_cli: use custom command line interface
    :param debug: if true, output will be printed to console
    """
    if not os.access(jar, os.R_OK):
        raise ValueError("Can not access JAR File: %s" % jar)

    if not os.access(config, os.R_OK):
        raise ValueError("Can not access config File: %s" % config)

    if worker_id >= workers:
        raise ValueError("Worker ID must be smaller than number of workers (starts at 0).")

    if not os.path.exists("eval-runs"):
        makedirs("eval-runs")

    for i in range(runs):
        if i % workers != worker_id:
            continue

        run_dir = "eval-runs/%03d" % i

        if os.path.exists(run_dir) and not overwrite:
            print("Run %s already exists, skipping." % run_dir)
            continue

        run_args = args(i) if callable(args) else args

        # Similar custom cli interface as calibration
        if custom_cli:
            cmd = custom_cli(jvm_args, jar, config, run_dir, i, seed + i, run_args)
        else:
            cmd = "java %s -jar %s run --config %s --output %s --runId %03d --config:global.randomSeed=%d %s" \
                  % (jvm_args, jar, config, run_dir, i, seed + i, run_args)

        # Extra whitespaces will break argument parsing
        cmd = cmd.strip()

        print("Running cmd %s" % cmd)

        if os.name != 'nt':
            cmd = cmd.split(" ")
            cmd = [c for c in cmd if c != ""]

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
                    print("Alternatively run the cmd from the log above manually and check for errors.",
                          file=sys.stderr)

                raise Exception("Process returned with error code: %s." % p.returncode)
        finally:
            p.terminate()

    process_results("eval-runs")


def setup(parser: argparse.ArgumentParser):
    parser.add_argument("--jar", type=str, required=True, help="Path to executable JAR file")
    parser.add_argument("--config", type=str, required=True, help="Path to config file")
    parser.add_argument("--args", type=str, default="", help="Arguments to pass to the simulation")
    parser.add_argument("--jvm-args", type=str, default="", help="Arguments to pass to the JVM")
    parser.add_argument("--runs", type=int, default=10, help="Number of simulations to run")
    parser.add_argument("--worker-id", type=int, default=0, help="ID of this worker")
    parser.add_argument("--workers", type=int, default=1, help="Total number of workers")
    parser.add_argument("--seed", type=int, default=4711, help="Starting seed")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output directories")
    parser.add_argument("--debug", action="store_true", help="Print output to console")


def main(args):
    run(args.jar, args.config, args.args, args.jvm_args, args.runs, args.worker_id, args.workers, args.seed,
        args.overwrite, debug=args.debug)
