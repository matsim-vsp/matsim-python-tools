#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import subprocess
import sys
from os import makedirs
from time import sleep
from typing import Union, Callable

METADATA = "run-simulations", "Utility to run multiple simulations at once."


def process_results(directory):
    """Process results of multiple simulations"""

    print("Processing results in %s" % directory)


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

    if not os.path.exists("eval-runs"):
        makedirs("eval-runs")

    for i in range(runs):
        if i % workers != worker_id:
            continue

        run_dir = "eval-runs/%03d" % i

        if os.path.exists(run_dir) and not overwrite:
            print("Run %s already exists, skipping." % run_dir)
            continue

        run_args = args(completed) if callable(args) else args

        # Same custom cli interface as calibration
        if custom_cli:
            cmd = custom_cli(jvm_args, jar, config, params_path, run_dir, trial.number, run_args)
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

    process_results("eval_runs")


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
