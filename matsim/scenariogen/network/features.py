#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from collections import defaultdict

import lxml.etree as ET
import pandas as pd
from shapely.geometry import LineString


def build_datasets(network, inter, routes):
    """ Build all datasets needed for training models"""
    ft = pd.read_csv(network)

    df_i = pd.read_csv(inter)
    df_i = pd.merge(df_i, ft, left_on="fromEdgeId", right_on="edgeId")

    df_r = pd.read_csv(routes).drop(columns=["speed"])
    df_r = pd.merge(df_r, ft, left_on="edgeId", right_on="edgeId")

    result = {}

    aggr = df_r.groupby(["junctionType"])
    for g in aggr.groups:
        if str(g) == "dead_end":
            continue

        result["speedRelative_" + str(g)] = prepare_dataframe(aggr.get_group(g), target="speedRelative")

    aggr = df_i.groupby(["junctionType"])
    df_i["norm_cap"] = df_i.capacity / df_i.numLanes
    for g in aggr.groups:
        result["capacity_" + str(g)] = prepare_dataframe(aggr.get_group(g), target="norm_cap")

    return result


def prepare_dataframe(df, target):
    """ Simple preprocessing """

    df = df.rename(columns={target: "target"})

    # Drop length outliers
    df = df[df.length < 500]

    # drop 2.5% smallest and largest
    drop = len(df) // 40
    df = df.drop(df.nsmallest(drop, ["target"]).index)
    df = df.drop(df.nlargest(drop, ["target"]).index)

    s = df['target']
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    iqr_lower = q1 - 1.5 * iqr
    iqr_upper = q3 + 1.5 * iqr
    outliers = s[(s < iqr_lower) | (s > iqr_upper)]

    df = df.drop(outliers.index)

    # remove unneeded features
    df = df[["target", "length", "speed",
             "dir_l", "dir_r", "dir_s", "dir_multiple_s", "dir_exclusive",
             "priority_lower", "priority_equal", "priority_higher",
             "numFoes", "numLanes", "changeNumLanes", "junctionSize"]]

    return df


def parse_ls(el):
    shape = el.attrib['shape']
    coords = [tuple(map(float, l.split(","))) for l in shape.split(" ")]
    return LineString(coords)


def combine_bitset(a, b):
    return "".join("1" if x[0] == "1" or x[1] == "1" else "0" for x in zip(a, b))


def read_network(sumo_network):
    """ Read sumo network from xml file. """

    edges = {}
    junctions = {}

    to_edges = defaultdict(lambda: [])

    # Aggregated connections, for outgoing edge
    connections = {}

    # count the indices of connections, assuming they are ordered
    # this seems to be the case according to sumo doc. there is no further index attribute
    idx = {}

    data_conns = []

    for _, elem in ET.iterparse(sumo_network, events=("end",),
                                tag=('edge', 'junction', 'connection'),
                                remove_blank_text=True):

        if elem.tag == "edge":
            edges[elem.attrib["id"]] = elem
            to_edges[elem.attrib["to"]].append(elem)
            continue

        elif elem.tag == "junction":
            junctions[elem.attrib["id"]] = elem
            idx[elem.attrib["id"]] = 0
            continue

        if elem.tag != "connection":
            continue

        # Rest is parsing connection        
        conn = elem.attrib

        fromEdge = edges[conn["from"]]
        fromLane = fromEdge.find("lane", {"index": conn["fromLane"]})

        toEdge = edges[conn["to"]]
        toLane = toEdge.find("lane", {"index": conn["toLane"]})

        junction = junctions[fromEdge.attrib["to"]]
        request = junction.find("request", {"index": str(idx[fromEdge.attrib["to"]])})

        # increase request index
        idx[fromEdge.attrib["to"]] += 1

        from_edge_id = fromEdge.attrib["id"]

        # Remove turn directions, which are not so relevant
        if conn["dir"] == "t":
            conn["dir"] = ""

        dirs = set(conn["dir"].lower())
        to = conn["fromLane"] + "_" + conn["to"] + "_" + conn["toLane"]

        if from_edge_id not in connections:
            connections[from_edge_id] = {
                "dirs": dirs,
                "response": request.attrib["response"],
                "foes": request.attrib["foes"],
                "to": {conn["to"]},
                "conns": 1,
                "dir_s": {to} if "s" in dirs else set(),
                "dir_exclusive": True
            }
        else:

            # Multiple direction connect straight
            if "s" in dirs:
                connections[from_edge_id]["dir_s"].add(to)

            if connections[from_edge_id]["dirs"].intersection(dirs):
                connections[from_edge_id]["dir_exclusive"] = False

            connections[from_edge_id]["dirs"].update(dirs)
            connections[from_edge_id]["response"] = combine_bitset(connections[from_edge_id]["response"],
                                                                   request.attrib["response"])
            connections[from_edge_id]["foes"] = combine_bitset(connections[from_edge_id]["foes"],
                                                               request.attrib["foes"])
            connections[from_edge_id]["to"].add(conn["to"])
            connections[from_edge_id]["conns"] += 1

        data_conns.append({
            "junctionId": junction.attrib["id"],
            "fromEdgeId": from_edge_id,
            "toEdgeId": toEdge.attrib["id"],
            "fromLaneId": fromLane.attrib["id"],
            "toLaneId": toLane.attrib["id"],
            "dir": conn["dir"],
            "connDistance": round(parse_ls(fromLane).distance(parse_ls(toLane)), 2)
        })

    data = []

    for edge in edges.values():
        junction = junctions[edge.attrib["to"]]

        conn = connections.get(edge.attrib["id"], {})

        # speed and length should be the same on all lanes
        lane = edge.find("lane", {"index": "0"})

        prio = int(edge.attrib["priority"])

        # determine priority relative to other edges
        prios = sorted(list(set(int(t.attrib["priority"]) for t in to_edges[edge.attrib["to"]])))

        ref = (len(prios) - 1) / 2
        cmp = prios.index(prio)
        if cmp > ref:
            prio = "higher"
        elif cmp < ref:
            prio = "lower"
        else:
            prio = "equal"

        dirs = conn.get("dirs", "")

        # Remove uncommon speed values close together
        speed = float(lane.attrib["speed"])
        speed = max(8.33, speed)

        num_lanes = len(edge.findall("lane"))
        num_to_lanes = max(len(edges[x].findall("lane")) for x in conn.get("to", [])) if "to" in conn else num_lanes

        d = {
            "edgeId": edge.attrib["id"],
            "edgeType": edge.attrib["type"].replace("highway.", ""),
            "priority": prio,
            "speed": speed,
            "length": float(lane.attrib["length"]),
            "numLanes": num_lanes,
            "changeNumLanes": min(num_to_lanes - num_lanes, 3),
            "numConns": min(conn.get("conns", 0), 6),
            "numResponse": min(conn.get("response", "").count("1"), 3),
            "numFoes": min(conn.get("foes", "").count("1"), 3),
            "dir_multiple_s": len(conn.get("dir_s", [])) > 1,
            "dir_l": "l" in dirs,
            "dir_r": "r" in dirs,
            "dir_s": "s" in dirs,
            "dir_exclusive": conn.get("dir_exclusive", True),
            "junctionType": junction.attrib["type"],
            "junctionSize": min(len(junction.findall("request")), 36)
        }

        data.append(d)

    df = pd.DataFrame(data)
    return pd.get_dummies(df, columns=["priority"]), pd.DataFrame(data_conns)


def read_edges(folder):
    """ Combine resulting files for edges """

    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        df = pd.read_csv(os.path.join(folder, f))
        edge_id = df.iloc[0].edgeId

        aggr = df.groupby("laneId").agg(capacity=("flow", "max"))

        data.append({
            "edgeId": edge_id,
            "capacity": float(aggr.capacity.mean())
        })

    return pd.DataFrame(data)


def read_intersections(folder):
    """ Read intersection results """

    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        try:
            df = pd.read_csv(os.path.join(folder, f))
        except pd.errors.EmptyDataError:
            print("Empty csv", f)
            continue

        # there could be exclusive lanes and the capacity to two edges completely additive
        # however if the capacity is shared one direction could use way more than physical possible
        aggr = df.groupby("fromEdgeId").agg(capacity=("flow", "max")).reset_index()
        aggr.rename(columns={"fromEdgeId": "edgeId"})

        data.append(aggr)

    return pd.concat(data)


def read_routes(folder):
    """ Read routes from folder """
    data = []
    for f in os.listdir(folder):
        if not f.endswith(".csv"):
            continue

        try:
            df = pd.read_csv(os.path.join(folder, f))
        except pd.errors.EmptyDataError:
            print("Empty csv", f)
            continue

        data.append(df)

    df = pd.concat(data)
    aggr = df.groupby("edgeId").mean()

    return aggr.reset_index()
