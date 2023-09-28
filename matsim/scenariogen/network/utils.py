#!/usr/bin/env python

import os
import sys
from subprocess import call

from shapely import wkt
from shapely.ops import transform

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)

def setup_parser(parser):
    parser.add_argument("input", nargs=1, help="Path to input csv")

    parser.add_argument("--output", default="output", help="Path to output folder")
    parser.add_argument("--network", type=str, default="../../../../scenarios/input/sumo.net.xml",
                        help="Path to network file")
    parser.add_argument("--veh", type=int, default=5000, help="Vehicles per hour per lane to simulate")
    parser.add_argument("--scenario", type=str, default="base", choices=["base", "sst", "st", "mt", "lt"],
                        help="Name of scenario for vehicle share and capabilities")
    parser.add_argument("--from-index", type=int, default=0, help="Start from number")
    parser.add_argument("--to-index", type=int, default=-1, help="Stop at number")
    parser.add_argument("--step-length", type=float, default=0.2, help="SUMO step length")
    parser.add_argument("--runner", type=str, default="runner0", help="Runner name")
    parser.add_argument("--runner-total", type=int, default=0, help="Total number of runners")
    parser.add_argument("--runner-index", type=int, default=0, help="Runner index")


def create_args(args):
    import sumolib

    args.port = sumolib.miscutils.getFreeSocketPort()

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(args.runner, exist_ok=True)

    return args

def vehicle_parameter(scenario):
    """ Predefined scenarios for vehicle parameters """

    if scenario == "base":
        return """
            <vType id="vehCV" probability="0.99" color="1,0,0" vClass="passenger" impatience="0.1"/>
            <vType id="vehAV" probability="0.01" color="0,1,0" vClass="passenger" decel="3.0" sigma="0.1" tau="1.5" speedFactor="1" speedDev="0" />
        """

    elif scenario == "sst":
        return """
            <vType id="vehCV" probability="0.9" color="1,0,0" vClass="passenger" impatience="0.1"/>
            <vType id="vehAV" probability="0.1" color="0,1,0" vClass="passenger" decel="3.0" sigma="0.1" tau="1.3" speedFactor="1" speedDev="0" />
        """

    elif scenario == "st":  # 5-10 years
        return """
            <vType id="vehCV" probability="0.7" color="1,0,0" vClass="passenger" impatience="0.1"/>
            <vType id="vehAV" probability="0.3" color="0,1,0" vClass="passenger" decel="3.0" sigma="0.1" tau="1.2" speedFactor="1" speedDev="0" />
        """
    elif scenario == "mt":  # 15-20 years
        return """
            <vType id="vehCV" probability="0.3" color="1,0,0" vClass="passenger" impatience="0.1"/>
            <vType id="vehAV" probability="0.55" color="0,1,0" vClass="passenger" decel="4.5" sigma="0.05" tau="0.9" speedFactor="1" speedDev="0" />
            <vType id="vehACV" probability="0.15" color="0,0,1" vClass="passenger" minGap="1" accel="2.6" decel="4.5" sigma="0.05" tau="0.8" speedFactor="1" speedDev="0" impatience="0"/>
        """
    elif scenario == "lt":  # 25+ years
        return """
            <vType id="vehCV" probability="0.05" color="1,0,0" vClass="passenger" impatience="0.1"/>
            <vType id="vehAV" probability="0.15" color="0,1,0" vClass="passenger" decel="4.5" sigma="0.05" tau="0.9" speedFactor="1" speedDev="0" />
            <vType id="vehACV" probability="0.8" color="0,0,1" vClass="passenger" minGap="0.5" accel="2.6" decel="4.5" sigma="0" tau="0.6" speedFactor="1" speedDev="0" impatience="0.8"/>
    """

    raise Exception("Unknown scenario: " + scenario)


def init_workload(args, items):
    """ Set indices for the runner automatically """
    if args.runner_total <= 1:
        return

    n = len(items)
    step = n // args.runner_total

    args.from_index = args.runner_index * step
    args.to_index = min((args.runner_index + 1) * step, n)


def write_scenario(f, network_file, route_file, additional_file, step_length=0.2, time=600):
    """ Write sumo scenario file """

    with open(f, "w") as fn:
        fn.write("""<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">

    <input>
        <net-file value="%s"/>
        <route-files value="%s"/>
        <additional-files value="%s"/>
    </input>

    <time>
        <begin value="0"/>
        <end value="%d"/>
        <step-length value="%f"/>
    </time>
</configuration>
""" % (network_file, route_file, additional_file, time, step_length))


def filter_network(netconvert, netfile, edge, output, args=None):
    if isinstance(edge, list):
        x = [s[0] for e in edge for s in e.getShape()]
        y = [s[1] for e in edge for s in e.getShape()]
    else:
        x = [s[0] for s in edge.getShape()]
        y = [s[1] for s in edge.getShape()]

    # minX,minY,maxX,maxY
    boundary = ",".join(str(s) for s in [min(x) - 50, min(y) - 50, max(x) + 50, max(y) + 50])

    cmd = [netconvert, '-s', netfile, "--keep-edges.in-boundary", boundary]

    if args:
        cmd += args

    cmd += ['-o', output]

    call(cmd)


def filter_network_polygon(netconvert, netfile, location_offset, geometry, output):
    """ Filter network with a list of polygon coordinates"""

    polygon = wkt.loads(geometry)

    polygon = transform(lambda x, y: (x + location_offset[0], y + location_offset[1]), polygon)

    coords = ",".join("%.2f,%.2f" % f for f in polygon.exterior.coords)

    cmd = [netconvert, '-s', netfile, "--keep-edges.in-boundary", coords, "--no-internal-links", "false"]
    cmd += ['-o', output]

    call(cmd)