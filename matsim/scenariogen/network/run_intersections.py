#!/usr/bin/env python
# @author  Angelo Banse, Ronald Nippold, Christian Rakow

import os
import shutil
import sys
from argparse import ArgumentParser
from os.path import join, basename

from .utils import setup_parser, create_args, init_workload, write_scenario, filter_network, vehicle_parameter

import traci  # noqa
import sumolib.net
from sumolib import checkBinary  # noqa
import lxml.etree as ET

import pandas as pd

sumoBinary = checkBinary('sumo')
netconvert = checkBinary('netconvert')

METADATA = "sumo-intersections", "Determine intersection volumes with SUMO."


def writeRouteFile(f_name, routes, extra_routes, scenario):
    """ Write route file for intersection """

    text = """<?xml version="1.0" encoding="UTF-8"?>

<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">


"""
    text += """<vTypeDistribution id="vDist">
                    %s
                </vTypeDistribution>
            """ % vehicle_parameter(scenario)

    for i, edges in enumerate(routes):
        text += """
            <flow id="veh%d" begin="0" end="1800" vehsPerHour="5000" type="vDist" departLane="best" arrivalLane="current" departSpeed="max">
               <route edges="%s"/>
            </flow>
        """ % (i, edges)

    for i, edges in enumerate(extra_routes):
        text += """
            <flow id="vehx%d" begin="0" end="1800" vehsPerHour="200" type="vDist" departLane="best" arrivalLane="current" departSpeed="max">
               <route edges="%s"/>
            </flow>
        """ % (i, edges)

    text += "</routes>"

    with open(f_name, "w") as f:
        f.write(text)


def writeDetectorFile(f_name, output, lanes):
    text = """<?xml version="1.0" encoding="UTF-8"?>
        <additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
"""

    for i, lane in enumerate(lanes):
        text += """
        <e1Detector id="detector%d" lane="%s" pos="-1" friendlyPos="true" freq="10.00" file="%s.xml"/>
    """ % (i, lane, join(output, "lane%d" % i))

    text += "</additional>"

    with open(f_name, 'w') as f:
        f.write(text)


def read_result(folder, junctionId, fromEdgeId, toEdgeId):

    res = []

    for f in os.listdir(folder):
        if not f.endswith(".xml"):
            continue

        total = 0
        end = 0
        lane = 0

        for _, elem in ET.iterparse(join(folder, f), events=("end",),
                                    tag=('interval',),
                                    remove_blank_text=True):

            begin = float(elem.attrib["begin"])
            end = float(elem.attrib["end"])
            if begin < 60:
                continue

            total = float(elem.attrib["nVehContrib"])

        flow = total * (3600 / (end - 60))

        res.append({
            "junctionId": junctionId,
            "fromEdgeId": fromEdgeId,
            "toEdgeId": toEdgeId,
            "lane": lane,
            "flow": flow
        })

        lane += 1

    return res


def run(args, nodes):
    print("Running scenario: " + args.scenario)

    if args.to_index <= 0:
        args.to_index = len(nodes)

    i = 0

    for x in range(args.from_index, args.to_index):
        node = nodes[x]
        i += 1

        print("####################################################################")
        print("Junction id: " + node._id)

        folder = join(args.runner, "detector")
        p_network = join(args.runner, "filtered.net.xml")

        edges = [c.getFrom() for c in node.getConnections()] + [c.getTo() for c in node.getConnections()]

        filter_network(netconvert, args.network, edges, p_network, ["--no-internal-links", "false"])

        pairs = set((c.getFrom(), c.getTo()) for c in node.getConnections() if c._direction != c.LINKDIR_TURN)

        res = []

        for fromEdge, toEdge in pairs:

            # Clean old data
            shutil.rmtree(folder, ignore_errors=True)
            os.makedirs(folder, exist_ok=True)

            p_scenario = join(args.runner, "scenario.sumocfg")
            p_routes = join(args.runner, "route.rou.xml")
            p_detector = join(args.runner, "detector.add.xml")

            routes = []

            # Build routes by trying to use incoming edge, when it is too short
            if fromEdge._length < 30:
                routes = [k._id + " " + fromEdge._id + " " + toEdge._id for k, v in fromEdge._incoming.items() if
                          all(d._direction not in (d.LINKDIR_TURN, d.LINKDIR_LEFT, d.LINKDIR_RIGHT) for d in v)]

            if not routes:
                routes = [fromEdge._id + " " + toEdge._id]

            extra_routes = []
            # Produce car traffic on the other connections
            for c in node.getConnections():
                if c._direction == c.LINKDIR_TURN:
                    continue

                if c.getFrom() == fromEdge or c.getTo() == toEdge:
                    continue

                r = c.getFrom()._id + " " + c.getTo()._id
                if r not in extra_routes:
                    extra_routes.append(r)

            lanes = [fromEdge._id + "_" + str(i) for i in range(len(fromEdge._lanes))]

            writeRouteFile(p_routes, routes, extra_routes, args.scenario)

            writeDetectorFile(p_detector, "detector", lanes)

            write_scenario(p_scenario, basename(p_network), basename(p_routes), basename(p_detector), args.step_length,
                           time=1800)

            go(p_scenario, args)

            # Read output
            res.extend(read_result(folder,
                                   junctionId=node._id,
                                   fromEdgeId=fromEdge._id,
                                   toEdgeId=toEdge._id))

        df = pd.DataFrame(res)
        df.to_csv(join(args.output, "%s.csv" % node._id), index=False)

        print("####################################################################")
        print("[" + str(i) + " / " + str(args.to_index - args.from_index) + "]")


def go(scenario, args):
    traci.start([sumoBinary, "-c", scenario])

    end = int(1800 * (1 / args.step_length))

    try:
        for step in range(0, end):
            traci.simulationStep()
    except Exception as e:
        print(e)

    traci.close()
    sys.stdout.flush()


def setup(parser: ArgumentParser):
    setup_parser(parser)


def main(args):
    args = create_args(args)

    # read in intersections
    with open(args.input[0]) as f:
        selection = set(f.read().splitlines())

    net = sumolib.net.readNet(args.network, withConnections=True, withInternal=False, withFoes=False)
    allNodes = net.getNodes()  # all type of nodes

    traffic_intersections = []
    for node in allNodes:
        if node._type != "internal" and node._id in selection:
            traffic_intersections.append(node)

    print("Total number of junctions:", len(traffic_intersections))

    init_workload(args, traffic_intersections)

    print("Processing: ", args.from_index, ' to ', args.to_index)

    run(args, traffic_intersections)


if __name__ == "__main__":
    parser = ArgumentParser(prog=METADATA[0], description=METADATA[1])
    setup(parser)
    main(parser.parse_args())

