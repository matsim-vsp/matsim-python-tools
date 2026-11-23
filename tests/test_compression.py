import gzip

import pandas as pd
import pytest
import zstandard

import matsim.Network
from matsim.calibration.analysis import read_trips_and_persons
from matsim.utils import find_file, glob_file


def to_zst(src, dst):
    with gzip.open(src, "rb") as f:
        dst.write_bytes(zstandard.ZstdCompressor().compress(f.read()))


def test_find_file(tmp_path):
    (tmp_path / "output_plans.xml.zst").touch()
    (tmp_path / "output_network.xml").touch()

    assert find_file(tmp_path / "output_plans.xml") == str(tmp_path / "output_plans.xml.zst")
    assert find_file(tmp_path / "output_plans.xml.gz") == str(tmp_path / "output_plans.xml.zst")
    assert find_file(tmp_path / "output_network.xml.gz") == str(tmp_path / "output_network.xml")

    with pytest.raises(FileNotFoundError):
        find_file(tmp_path / "output_events.xml")


def test_glob_file(tmp_path):
    (tmp_path / "run.output_trips.csv.zst").touch()

    assert glob_file(tmp_path, "*.output_trips.csv") == str(tmp_path / "run.output_trips.csv.zst")
    assert glob_file(tmp_path, "*.output_trips.csv.gz") == str(tmp_path / "run.output_trips.csv.zst")

    with pytest.raises(FileNotFoundError):
        glob_file(tmp_path, "*.output_persons.csv")


def test_read_zst_network(tmp_path):
    to_zst("tests/test_network.xml.gz", tmp_path / "network.xml.zst")

    # The gz name is resolved to the zst file
    network = matsim.Network.read_network(str(tmp_path / "network.xml.gz"))
    assert len(network.nodes) == 15
    assert len(network.links) == 23


def test_read_zst_run_output(tmp_path):
    trips = pd.DataFrame({"person": ["1", "1"], "trip_number": [1, 2],
                          "main_mode": ["car", None], "longest_distance_mode": ["car", "walk"]})
    persons = pd.DataFrame({"person": ["1"], "first_act_x": [0.0], "first_act_y": [0.0]})

    trips.to_csv(tmp_path / "run.output_trips.csv.zst", sep=";", index=False)
    persons.to_csv(tmp_path / "run.output_persons.csv.zst", sep=";", index=False)

    df, _ = read_trips_and_persons(str(tmp_path))
    assert list(df.main_mode) == ["car", "walk"]
