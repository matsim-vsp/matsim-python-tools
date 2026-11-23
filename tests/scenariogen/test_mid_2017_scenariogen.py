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

    print(pd.read_csv("tests/scenariogen/mid2017/test_output/table-households.csv"))

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)

    actual_households = pd.read_csv("tests/scenariogen/mid2017/test_output/table-households.csv")
    print("Shapes:", expected_households.shape, actual_households.shape)
    print("Expected dtypes:\n", expected_households.dtypes)
    print("Actual dtypes:\n", actual_households.dtypes)


    difference = expected_households.compare(
        actual_households,
        keep_shape=True,
        keep_equal=True,
        result_names=("expected", "actual"),
    )
    print(difference.to_string())

    print("Column difference:",
           set(expected_households.columns) ^ set(actual_households.columns))

    pd.testing.assert_frame_equal(
        expected_households,
        actual_households,
        check_exact=False,
        rtol=1e-9,
        atol=1e-12,
    )

    assert expected_activities.equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-activities.csv"))
    assert expected_households.equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-households.csv"))
    assert expected_persons.equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-persons.csv"))
    assert expected_trips.equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-trips.csv"))
    assert expected_unscaled_persons.equals(pd.read_csv("tests/scenariogen/mid2017/test_output/table-unscaled-persons.csv"))
