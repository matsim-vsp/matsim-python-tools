from unittest import TestCase

import matsim.Network


class TestNetworkHandler(TestCase):

    def test(self):
        network = matsim.Network.read_network('tests/test_network.xml.gz')

        # we know how many links and nodes the test network has
        self.assertEqual(15, len(network.nodes))
        self.assertEqual(23, len(network.links))

        # lets check for present of from and to node of link #1
        self.assertTrue('1' in network.nodes)
        self.assertTrue('2' in network.nodes)
        fromNode = network.nodes['1']
        toNode = network.nodes['2']
        self.assertEqual(-20000, fromNode.x)
        self.assertEqual(0, fromNode.y)
        self.assertEqual(1, len(fromNode.in_links))
        self.assertEqual(1, len(fromNode.out_links))
        self.assertEqual(1, len(toNode.in_links))
        self.assertEqual(9, len(toNode.out_links))

        # test link #1 with all its attributes
        self.assertTrue('1' in network.links)
        link = network.links['1']
        self.assertEqual(fromNode, link.from_node)
        self.assertEqual(toNode, link.to_node)
        self.assertEqual('1', link.id)
        self.assertEqual(36000, link.capacity)
        self.assertEqual(10000, link.length)
        self.assertEqual(27.78, link.freespeed)
        self.assertEqual(1, link.permlanes)
        self.assertListEqual(['car', 'bike'], link.modes)
