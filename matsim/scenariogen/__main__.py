#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

from .data import run_create_ref_data
from .data import run_extract_activities
from .data import run_lookup_regiostar
from .network import run_collect_results
from .network import run_edges as sumo_edges
from .network import run_intersections as sumo_intersections
from .network import run_routes as sumo_routes
from .network import run_train_model


def _add(subparsers, m):
    """ Adds module to as subcommand"""
    s1 = subparsers.add_parser(m.METADATA[0], help=m.METADATA[1])
    m.setup(s1)
    s1.set_defaults(func=m.main)


def main():
    """ Main entry point. """

    parser = argparse.ArgumentParser(prog='matsim-scenariogen',
                                     description="MATSim scenario command line utility")

    subparsers = parser.add_subparsers(title="Subcommands")

    _add(subparsers, sumo_edges)
    _add(subparsers, sumo_routes)
    _add(subparsers, sumo_intersections)
    _add(subparsers, run_train_model)
    _add(subparsers, run_collect_results)

    try:
        from .network import run_opt_freespeed
        _add(subparsers, run_opt_freespeed)
    except Exception as e:
        print("Opt freespeed not available", e)

    _add(subparsers, run_extract_activities)
    _add(subparsers, run_create_ref_data)
    _add(subparsers, run_lookup_regiostar)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
