#!/usr/bin/env python
# @author  Angelo Banse, Ronald Nippold, Christian Rakow

import os
import sys
from argparse import ArgumentParser
from os.path import join, basename
from traceback import print_exc

from .utils import init_workload, setup_parser, create_args, write_scenario, filter_network_polygon, vehicle_parameter

import sumolib.net
import traci  # noqa

from sumolib import checkBinary  # noqa
from randomTrips import get_options, main as gen_trips

import lxml.etree as ET

import pandas as pd

sumoBinary = checkBinary('sumo')
netconvert = checkBinary('netconvert')

METADATA = "sumo-routes", "Determine avg. uncongested link speed with SUMO."


def writeRouteFile(f_name, fromEdge, toEdge, veh, end, scenario):
    """ Write route file using flow """
    # https://sumo.dlr.de/docs/Demand/Shortest_or_Optimal_Path_Routing.html
    # https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#incomplete_routes_trips_and_flows

    text = f"""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <vTypeDistribution id="vDist">
        {vehicle_parameter(scenario)}
    </vTypeDistribution>
    <flow id="veh" begin="0" end="{end}" vehsPerHour="{veh}" type="vDist" from="{fromEdge}" to="{toEdge}" departSpeed="speedLimit"/>
    
</routes>
"""

    with open(f_name, "w") as f:
        f.write(text)


def writeDetectorFile(f_name, begin):
    """ Write files needed for analysis """

    # https://sumo.dlr.de/docs/Simulation/Output/Lane-_or_Edge-based_Traffic_Measures.html

    text = f"""<?xml version="1.0" encoding="UTF-8"?>
	<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
	    <edgeData id="out" file="out.xml" begin="%d" excludeEmpty="true"/>
	</additional>
	""" % begin

    with open(f_name, 'w') as f:
        f.write(text)


def read_result(out):
    """ Reads result from output xml """

    data = []

    for _, elem in ET.iterparse(out, events=("end",),
                                tag=('edge',),
                                remove_blank_text=True):
        d = {
            "edgeId": elem.attrib["id"]
        }
        for a in ("traveltime", "density", "waitingTime", "timeLoss", "speed", "speedRelative"):
            d[a] = float(elem.attrib.get(a, float("nan")))

        # Skip the non primary routes
        if int(elem.attrib.get("entered", "0")) < 100 and int(elem.attrib.get("left", "0")) < 100:
            continue

        data.append(d)

    return pd.DataFrame(data)


def run(args, routes, location_offset):
    i = 0

    if args.to_index <= 0:
        args.to_index = len(routes)

    for x in range(args.from_index, args.to_index):
        route = routes.iloc[x]
        i += 1

        print(route)

        p_network = join(args.runner, "filtered.net.xml")
        p_routes = join(args.runner, "route.rou.xml")
        p_detector = join(args.runner, "detector.add.xml")
        p_trips = join(args.runner, "trips.trips.xml")

        # 1hour simulation plus travel time
        end = int(route.travel_time + 3600)

        filter_network_polygon(netconvert, args.network, location_offset, route.geometry, p_network)

        # Nearly uncongested vehicle flow
        writeRouteFile(p_routes, route.fromEdge, route.toEdge, int(route.min_capacity * 0.3), end, args.scenario)
        writeDetectorFile(p_detector, route.travel_time)

        # Produce some very light traffic on the other roads
        gen_trips(get_options(["-n", p_network, "-o", p_trips, "-r", join(args.runner, "random_routes.rou.xml"),
                          "--validate", "-e", end, '-t type="vDist"',
                          "--insertion-density", args.insertion_density, "--fringe-factor", "max"]))

        p_scenario = join(args.runner, "scenario.sumocfg")

        write_scenario(p_scenario, basename(p_network), basename(p_routes) + "," + "trips.trips.xml",
                       basename(p_detector), args.step_length, end)

        try:
            go(p_scenario, p_network, end, route.fromEdge + "_" + route.toEdge, args)
        except Exception as e:
            print_exc()

        print("####################################################################")
        print("[" + str(i) + " / " + str(args.to_index - args.from_index) + "]")


def go(scenario, network, end, f, args):
    # Clean existing output
    out = join(args.runner, "out.xml")

    if os.path.exists(out):
        os.remove(out)

    traci.start([sumoBinary, "-n", network], port=args.port)

    steps = int(end * (1 / args.step_length))

    # Load scenario with desired traffic scaling
    traci.load(["-c", scenario])
    try:
        for step in range(0, steps):
            traci.simulationStep()
    except Exception as e:
        print(e)

    traci.close()

    res = read_result(out)
    res.to_csv(join(args.output, f + ".csv"), index=False)

    sys.stdout.flush()


def setup(parser: ArgumentParser):
    setup_parser(parser)

    parser.add_argument("--insertion-density", type=float, default=10, help="Density of background vehicles")


def main(args):

    args = create_args(args)

    # Net is needed to get the bounds
    net = sumolib.net.readNet(args.network, withConnections=False, withInternal=False, withFoes=False)

    df = pd.read_csv(args.input[0])

    init_workload(args, df)

    print("Total number of routes:", len(df))
    print("Processing: ", args.from_index, ' to ', args.to_index)

    run(args, df, net.getLocationOffset())


if __name__ == "__main__":
    parser = ArgumentParser(prog=METADATA[0], description=METADATA[1])
    setup(parser)
    main(parser.parse_args())

