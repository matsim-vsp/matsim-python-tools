from unittest import TestCase

import matsim.Network


class TestNetworkHandler(TestCase):

    def test(self):
        network = matsim.Network.read_network('tests/test_network.xml.gz')
        nodes = network.nodes
        links = network.links

        # we know how many links and nodes the test network has
        self.assertEqual(15, len(nodes))
        self.assertEqual(23, len(links))

        # lets check for present of from and to node of link #1
        self.assertTrue(len(nodes.node_id[nodes.node_id=='1']) == 1)
        self.assertTrue(len(nodes.node_id[nodes.node_id=='2']) == 1)

        fromNode = nodes[nodes.node_id == '1']
        self.assertEqual(-20000, fromNode.x[0])
        self.assertEqual(0, fromNode.y[0])

        # test link #1 with all its attributes
        self.assertTrue(len(links.link_id[links.link_id=='1']) == 1)
        link = links[links.link_id == '1']

        self.assertEqual('1', link.from_node[0])
        self.assertEqual('2', link.to_node[0])
        self.assertEqual('1', link.link_id[0])
        self.assertEqual(36000, link.capacity[0])
        self.assertEqual(10000, link.length[0])
        self.assertEqual(27.78, link.freespeed[0])
        self.assertEqual(1, link.permlanes[0])
        self.assertEqual('car,bike', link.modes[0])
