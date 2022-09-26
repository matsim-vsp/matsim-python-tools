#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser

import clean_iters as ci

def main():
    """ Main entry point. """

    parser = ArgumentParser(prog='matsim-tools', description="MATSim ommand line util")
    subparsers = parser.add_subparsers(title="Subcommands")

    s1 = subparsers.add_parser(ci.METADATA[0], help=ci.METADATA[1])
    ci.setup(s1)
    s1.set_defaults(func=ci.main)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()