#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import run_create_csv
from . import run_simulations

def _add(subparsers, m):
    """ Adds module to as subcommand"""
    s1 = subparsers.add_parser(m.METADATA[0], help=m.METADATA[1])
    m.setup(s1)
    s1.set_defaults(func=m.main)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="matsim-calibration", description="MATSim calibration command line utility")

    subparsers = parser.add_subparsers(title="Subcommands")

    _add(subparsers, run_create_csv)
    _add(subparsers, run_simulations)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
    else:
        args.func(args)

