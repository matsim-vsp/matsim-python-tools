# -*- coding: utf-8 -*-

from unittest import TestCase

from assertpy import assert_that

from matsim.io import read_pb, to_pandas


class IoTest(TestCase):

    def test_read_pb(self):
        events = list(read_pb("test_events.pb.gz"))

        assert_that(events).is_length(2000)

        for ev in events:
            assert_that(ev.time).is_greater_than_or_equal_to(0)

    def test_to_pandas(self):
        events = read_pb("test_events.pb.gz")
        df = to_pandas(events)

        assert_that(df).is_length(2000)
