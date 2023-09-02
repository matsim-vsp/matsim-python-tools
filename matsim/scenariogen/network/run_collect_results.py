#!/usr/bin/env python

import os

from argparse import ArgumentParser

from .features import read_edges, read_intersections, read_routes

METADATA = "sumo-collect-results", "Aggregate results from sumo runs"


def setup(parser: ArgumentParser):

    parser.add_argument("mode", nargs='?', help="Convert result file that create with one of the run scripts",
                        choices=["edges", "intersections", "routes"])
    parser.add_argument("--input", help="Path to input file for conversion")

def main(args):

    df = None

    if args.input:

        if args.mode == "edges":
            df = read_edges(args.input)

        elif args.mode == "intersections":
            df = read_intersections(args.input)

        elif args.mode == "routes":
            df = read_routes(args.input)

        if df is not None:
            base = os.path.basename(args.input.rstrip("/"))
            df.to_csv(f"result_{args.mode}_{base}.csv", index=False)

    else:
        print("Skipping results, because --input is not given")