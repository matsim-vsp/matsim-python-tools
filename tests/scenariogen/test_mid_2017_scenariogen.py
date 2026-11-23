import argparse
import os

import pandas as pd

from matsim.scenariogen.data import run_extract_activities



def test_mid_2017():
    os.makedirs("tests/scenariogen/mid2017/test_output", exist_ok=True)
    args = argparse.Namespace(dirs=["tests/scenariogen/mid2017"], regiostar=None, output="tests/scenariogen/mid2017/test_output/table")
    run_extract_activities.main(args)

    expected_activities = pd.read_csv("tests/scenariogen/mid2017/expected_output/table-activities.csv")
    expected_households = pd.read_csv("tests/scenariogen/mid2017/expected_output/table-households.csv")
    expected_persons = pd.read_csv("tests/scenariogen/mid2017/expected_output/table-persons.csv")
    expected_trips = pd.read_csv("tests/scenariogen/mid2017/expected_output/table-trips.csv")
    expected_unscaled_persons = pd.read_csv("tests/scenariogen/mid2017/expected_output/table-unscaled-persons.csv")

    assert expected_activities.equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-activities.csv"))
    # We cannot compare the geom column, since it seems to have slightly different values depending on the environment.
    # And since it is a string, we cannot compare it with a tolerance.
    assert expected_households.drop("geom", axis=1).equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-households.csv").drop("geom", axis=1))
    # Same for persons
    assert expected_persons.drop("geom", axis=1).equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-persons.csv").drop("geom", axis=1))
    assert expected_trips.equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-trips.csv"))
    assert expected_unscaled_persons.equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-unscaled-persons.csv"))
