import argparse

import pandas as pd

from matsim.scenariogen.data import run_extract_activities


def test_srv_2018():
    args = argparse.Namespace(dirs=["tests/scenariogen"], regiostar=None, output="tests/scenariogen/test_output/table")
    run_extract_activities.main(args)

    expected_activities = pd.read_csv("tests/scenariogen/expected_output/table-activities.csv")
    expected_households = pd.read_csv("tests/scenariogen/expected_output/table-households.csv")
    expected_persons = pd.read_csv("tests/scenariogen/expected_output/table-persons.csv")
    expected_trips = pd.read_csv("tests/scenariogen/expected_output/table-trips.csv")
    expected_unscaled_persons = pd.read_csv("tests/scenariogen/expected_output/table-unscaled-persons.csv")

    assert expected_activities.equals(pd.read_csv("tests/scenariogen/test_output/table-activities.csv"))
    assert expected_households.equals(pd.read_csv("tests/scenariogen/test_output/table-households.csv"))
    assert expected_persons.equals(pd.read_csv("tests/scenariogen/test_output/table-persons.csv"))
    assert expected_trips.equals(pd.read_csv("tests/scenariogen/test_output/table-trips.csv"))
    assert expected_unscaled_persons.equals(pd.read_csv("tests/scenariogen/test_output/table-unscaled-persons.csv"))
