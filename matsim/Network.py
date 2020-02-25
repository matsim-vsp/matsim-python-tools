import gzip
import xml.sax
from xml import sax


class Entity:

    def __init__(self, entity_id):
        self.id = entity_id


class Node(Entity):

    def __init__(self, entity_id, x, y):
        super().__init__(entity_id)
        self.x = float(x)
        self.y = float(y)
        self.in_links = set()
        self.out_links = set()

    def add_in_link(self, link):
        self.in_links.add(link)

    def add_out_link(self, link):
        self.out_links.add(link)


class Link(Entity):

    def __init__(self, entity_id, from_node, to_node, length, capacity, freespeed, permlanes, modes):
        super().__init__(entity_id)
        self.modes = modes
        self.permlanes = float(permlanes)
        self.freespeed = float(freespeed)
        self.capacity = float(capacity)
        self.length = float(length)
        self.to_node = to_node
        self.from_node = from_node


class Network:

    @property
    def links(self):
        return self._links.copy()

    @property
    def nodes(self):
        return self._nodes.copy()

    def __init__(self, nodes, links):
        self._nodes = nodes
        self._links = links

    @classmethod
    def from_links(cls, links):
        nodes = {}
        for link in links.values():
            # setdefault => f key is in the dictionary, return its value. If not, insert key with a value of default and return default. default defaults to None.
            from_node = nodes.setdefault(link.from_node.id, link.from_node)
            from_node.add_out_link(link)
            to_node = nodes.setdefault(link.to_node.id, link.to_node)
            to_node.add_in_link(link)

        return Network(nodes, links)


class NetworkHandler(xml.sax.ContentHandler):
    NODE = 'node'
    NODES = 'nodes'
    LINK = 'link'
    LINKS = 'links'

    def links(self):
        return self._links.copy()

    def nodes(self):
        return self._nodes.copy()

    def __init__(self):
        super().__init__()
        self._nodes = {}
        self._links = {}

    def startElement(self, name, attrs):
        if name == NetworkHandler.NODE:
            node = Node(attrs.get('id'), attrs.get('x'), attrs.get('y'))
            self._nodes[node.id] = node
        elif name == NetworkHandler.LINK:
            link = Link(attrs.get('id'),
                        self._nodes[attrs.get('from')],
                        self._nodes[attrs.get('to')],
                        attrs.get('length'),
                        attrs.get('capacity'),
                        attrs.get('freespeed'),
                        attrs.get('permlanes'),
                        str(attrs.get('modes')).split(','))
            self._links[link.id] = link
        else:
            print('start element', name, ' ', str(attrs))

    def characters(self, content):
        # don't do anything here, but skip all the characters to save some memory
        pass


""" Reads a Matsim network xml file. Currently, custom attributes are not parsed.
"""


def read(filepath):
    handler = NetworkHandler()
    with gzip.open(filepath) as file:
        sax.parse(file, handler)
    return Network.from_links(handler.links())
