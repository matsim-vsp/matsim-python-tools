import numpy as np

from matsim.calibration.calib_asc_dist import detect_dist_groups


def test_detect_dist_groups():
    groups = ["1000 - 2000", "2000+", "0 - 1000"]

    bins, labels = detect_dist_groups(groups)

    assert bins == [0, 1000, 2000, np.inf]
    assert labels == ["0 - 1000", "1000 - 2000", "2000+"]

    groups = ["1000 - 2000", "20000+", "0 - 1000", "2000 - 10000", "10000 - 20000"]

    bins, labels = detect_dist_groups(groups)

    assert bins == [0, 1000, 2000, 10000, 20000, np.inf]
    assert labels == ["0 - 1000", "1000 - 2000", "2000 - 10000", "10000 - 20000", "20000+"]
