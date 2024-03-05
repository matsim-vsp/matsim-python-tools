#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser


def start_piri(args):
    from matsim.viz import piri
    piri.app.run(debug=False)

def main():
    """ Main entry point. """

    parser = ArgumentParser(prog='matsim-viz', description="MATSim viz util")
    subparsers = parser.add_subparsers(title="Subcommands")

    # Because the dash app can not easily be separated, the command lne parser is duplicated here
    s1 = subparsers.add_parser("piri", help="Analyze the evolution of plans of a single agent or compare different agents side by side.")
    s1.add_argument("inputfile", help="Full path to the file containing the plan inheritance records, e.g. path/to/matsim/output/planInheritanceRecords.csv.gz")

    s1.set_defaults(func=start_piri)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
