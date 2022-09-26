#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Command line tool remove iterations directotries. See help usage for details:
    >> python3.9 clean_iters.py -h
"""

import re
import os
import shutil

from argparse import ArgumentParser


METADATA = "clean-iters", "Remove all iterations directories except the last one"

def setup(parser : ArgumentParser):
    
    parser.add_argument("dirs", nargs="+", help="Directories to scan")
    parser.add_argument("-f", "--force", action='store_true', default=False, help="Don't ask for confirmation")
    parser.add_argument("-d", "--dry-run", action='store_true', default=False, help="Don't remove anything, only print for information")

def main(args):

    pattern = re.compile(r"it\.(\d+)")

    for d in args.dirs:
        for dirpath, dirnames, filenames in os.walk(os.path.abspath(d)):

            matches = [pattern.match(it) for it in dirnames]
            
            iters = [(m.group(0), int(m.group(1)) ) for m in matches if m is not None]
            iters = sorted(iters, key=lambda k: k[1])

            if len(iters) > 1:

                print("Found %d iterations in %s" % (len(iters), dirpath))

                delete = False
                if args.dry_run:
                    delete = False
                elif args.force:
                    delete = True
                else:
                    answer = input("Delete [yn]?: ")
                    if any(answer.lower() == f for f in ["yes", 'y', '1', 'ye']):
                        delete = True
                    elif any(answer.lower() == f for f in ["no", 'n', '']):
                        delete = False
                    else:
                        print("Unknown answer, don't delete")

                if delete:

                    # Delete all except last
                    for iter, n in iters[:-1]:
                        path = os.path.join(dirpath, iter)
                        try:
                            shutil.rmtree(path)
                        except Exception as e:
                            print("Error removing %s:" % path, e)


if __name__ == "__main__":

    parser = ArgumentParser(prog=METADATA[0], description=METADATA[1])

    setup(parser)

    args= parser.parse_args()
    main(args)
