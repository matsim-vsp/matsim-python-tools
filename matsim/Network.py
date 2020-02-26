# -*- coding: utf-8 -*-

import gzip
import xml.etree.ElementTree as ET
import pandas as pd
import geopandas as gpd
import shapely.geometry as shp
from collections import namedtuple


class Network:

    def __init__(self, nodes, links, link_attrs, node_attrs):
        self.nodes = nodes
        self.links = links
        self.link_attrs = link_attrs
        self.node_attrs = node_attrs

    def as_geo_dataframe(self, projection):

        # attach xy to links
        full_net = (self.links
        .merge(self.nodes,
                left_on='from_node',
                right_on='node_id') # [['link_id', 'from_node', 'to_node', 'x', 'y']]
        .merge(self.nodes,
                left_on='to_node',
                right_on='node_id',
                suffixes=('_from_node', '_to_node')) # [['link_id', 'from_node', 'to_node','x_from_node', 'y_from_node','x_to_node', 'y_to_node']]
        )

        # create the geometry column from coordinates
        geometry = [shp.LineString([(ox,oy), (dx,dy)]) for ox, oy, dx, dy in zip(full_net.x_from_node, full_net.y_from_node, full_net.x_to_node, full_net.y_to_node)]

        # build the geopandas geodataframe
        geo_net = (gpd.GeoDataFrame(full_net,
            geometry=geometry,
            crs = {'init': projection})
            .drop(columns=['x_from_node','y_from_node','node_id_from_node','node_id_to_node','x_to_node','y_to_node'])
            )

        return geo_net

def read_network(filename, skip_attributes=False):
    tree = ET.iterparse(gzip.open(filename, 'r'))
    nodes = []
    links = []
    node_attrs = []
    link_attrs = []

    attributes = node_attrs
    attr_label = 'node_id'
    current_id = None

    for xml_event, elem in tree:
        # the nodes element CLOSES at the end of the nodes, followed by links:
        if elem.tag == 'nodes':
            attributes = link_attrs
            attr_label = 'link_id'

        elif elem.tag == 'node':
            atts = elem.attrib
            current_id = atts['id']

            atts['node_id'] = atts.pop('id')
            atts['x'] = float(atts['x'])
            atts['y'] = float(atts['y'])
            if 'z' in atts: atts['z'] = float(atts['z'])

            nodes.append(atts)

        elif elem.tag == 'link':
            atts = elem.attrib
            current_id = atts['id']

            atts['link_id'] = atts.pop('id')
            atts['from_node'] = atts.pop('from')
            atts['to_node'] = atts.pop('to')

            atts['length'] = float(atts['length'])
            atts['freespeed'] = float(atts['freespeed'])
            atts['capacity'] = float(atts['capacity'])
            atts['permlanes'] = float(atts['permlanes'])

            if 'volume' in atts: atts['volume'] = float(atts['volume'])

            links.append(atts)

        elif elem.tag == 'attribute':
            if not skip_attributes:
                atts = {}
                atts[attr_label] = current_id
                atts['name'] = elem.attrib['name']
                atts['value'] = elem.text

                # TODO: pandas will make the value column "object" since we're mixing types
                if 'class' in elem.attrib and elem.attrib['class'] == 'java.lang.Long':
                    atts['value'] = float(elem.text)

                attributes.append(atts)

        # clear the element when we're done, to keep memory usage low
        elem.clear()

    nodes = pd.DataFrame.from_records(nodes)
    links = pd.DataFrame.from_records(links)
    node_attrs = pd.DataFrame.from_records(node_attrs)
    link_attrs = pd.DataFrame.from_records(link_attrs)

    return Network(nodes, links, node_attrs, link_attrs)
