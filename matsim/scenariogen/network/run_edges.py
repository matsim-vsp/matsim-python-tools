#!/usr/bin/env python
# @author  Angelo Banse, Ronald Nippold, Christian Rakow

import os
import shutil
import sys
from argparse import ArgumentParser
from os.path import join, basename

from .utils import init_workload, setup_parser, create_args, write_scenario, filter_network, vehicle_parameter

import sumolib.net
import traci  # noqa
from sumolib import checkBinary  # noqa
import lxml.etree as ET

import pandas as pd
import numpy as np

sumoBinary = checkBinary('sumo')
netconvert = checkBinary('netconvert')

METADATA = "sumo-edges", "Determine edge volumes with SUMO."


def capacity_estimate(v):
    tT = 1.2
    lL = 7.0
    Qc = v / (v * tT + lL)

    return 3600 * Qc


def writeRouteFile(f_name, departLane, arrivalLane, edges, veh, scenario):
    text = """<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">

"""
    text += """<vTypeDistribution id="vDist">
                    %s
                </vTypeDistribution>
            """ % vehicle_parameter(scenario)

    text += """
    <flow id="veh" begin="0" end= "600" vehsPerHour="{veh}" type="vDist" departLane="{departLane}" arrivalLane="{arrivalLane}" departSpeed="max">
        <route edges="{edges}"/>
    </flow>

</routes>"""

    # departSpeed="speedLimit" ?
    context = {
        "departLane": departLane,
        "arrivalLane": arrivalLane,
        "edges": edges,
        "veh": veh
    }

    with open(f_name, "w") as f:
        f.write(text.format(**context))


def writeDetectorFile(f_name, output, lane, laneNr, scale):
    text = """<?xml version="1.0" encoding="UTF-8"?>

	<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
	        %s
	</additional>

	""" % "\n".join(
        """<e1Detector id="detector_%d" lane="{lane}_%d" pos="-15" friendlyPos="true" freq="10.00" file="{output_file}_%d.xml"/>""" % (
            i, i, i)
        for i in
        range(laneNr))

    context = {
        "lane": lane,
        "laneNr": laneNr,
        "output_file": join(output, scale, "lane")
    }

    with open(f_name, 'w') as f:
        f.write(text.format(**context))


def read_result(folder, edge, scale):
    data = []

    for f in os.listdir(folder):
        if not f.endswith(".xml"):
            continue

        total = 0
        end = 0

        for _, elem in ET.iterparse(join(folder, f), events=("end",),
                                    tag=('interval',),
                                    remove_blank_text=True):

            begin = float(elem.attrib["begin"])
            end = float(elem.attrib["end"])
            if begin < 60:
                continue

            total += float(elem.attrib["nVehContrib"])

        data.append({
            "edgeId": edge,
            "laneId": f.replace(".xml", ""),
            "flow": total * (3600 / (end - 60)),
            "scale": float(scale),
            "count": total
        })

    return data


def run(args, edges):
    # saveToFile(edges_ids,"junctions.json")
    i = 0

    if args.to_index <= 0:
        args.to_index = len(edges)

    for x in range(args.from_index, args.to_index):
        edge = edges[x]
        i += 1
        print("Edge id: ", edge._id)
        print("Number of lanes: ", edge.getLaneNumber(), "speed:", edge.getSpeed())

        laneNr = edge.getLaneNumber()  # nr of lanes

        cap = capacity_estimate(edge.getSpeed()) * 0.9 * laneNr

        print("Capacity estimate:", cap)

        p_network = join(args.runner, "filtered.net.xml")
        p_routes = join(args.runner, "route.rou.xml")
        p_detector = join(args.runner, "detector.add.xml")

        filter_network(netconvert, args.network, edge, p_network)
        writeRouteFile(p_routes, "best", "current", edge._id, cap, args.scenario)
        p_scenario = join(args.runner, "scenario.sumocfg")

        write_scenario(p_scenario, basename(p_network), basename(p_routes), basename(p_detector), args.step_length)

        go(p_scenario, p_network, edge, p_detector, args)
        print("####################################################################")
        print("[" + str(i) + " / " + str(args.to_index - args.from_index) + "]")


def go(scenario, network, edge, p_detector, args):
    # while traci.simulation.getMinExpectedNumber() > 0:

    end = int(600 * (1 / args.step_length))

    res = []

    folder = join(args.runner, "detector")

    # Clean old data
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder, exist_ok=True)

    traci.start([sumoBinary, "-n", network], port=args.port)

    xr = ["%.2f" % s for s in np.arange(1, 2.1, 0.05)]

    # Simulate different scales
    for scale in xr:

        # print("Running scale", scale)

        os.makedirs(join(folder, scale), exist_ok=True)
        writeDetectorFile(p_detector, "detector", edge._id, edge.getLaneNumber(), scale)

        # Load scenario with desired traffic scaling
        traci.load(["-c", scenario, "--scale", scale])

        try:
            for step in range(0, end):
                traci.simulationStep()
        except Exception as e:
            print(e)

    traci.close()

    for scale in xr:
        res.extend(read_result(join(folder, scale), edge._id, scale))

    df = pd.DataFrame(res)
    df.to_csv(join(args.output, "%s.csv" % edge._id), index=False)

    sys.stdout.flush()


def setup(parser: ArgumentParser):
    setup_parser(parser)


def main(args):
    args = create_args(args)

    net = sumolib.net.readNet(args.network, withConnections=False, withInternal=False, withFoes=False)

    allEdges = net.getEdges()  # all type of edges

    with open(args.input[0]) as f:
        selection = set(f.read().splitlines())

    # select if edges in net file
    edges = [edge for edge in allEdges if edge._id in selection]

    init_workload(args, edges)

    print("Total number of edges:", len(edges))
    print("Processing: ", args.from_index, ' to ', args.to_index)

    run(args, edges)


if __name__ == "__main__":
    parser = ArgumentParser(prog=METADATA[0], description=METADATA[1])
    setup(parser)
    main(parser.parse_args())
