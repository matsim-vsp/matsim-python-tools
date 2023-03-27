import gzip
import pathlib

import pytest

import numpy as np

from matsim.calibration import ASCSampler

def test_asc_sampler():

    # variables are not needed for this test
    sampler = ASCSampler(None, None, None, None, None)

    utils = np.random.rand(1000, 4)
    ascs = np.zeros(4)

    # real shares (target)
    z = [0.1, 0.5, 0.3, 0.1]

    # 100 iterations
    for it in range(200):

        modes = np.argmax(utils + ascs + np.random.normal(size=(1000, 4)), axis=1)
        _, counts = np.unique(modes, return_counts=True)

        share = counts / np.sum(counts)

        for i in range(1, len(share)):
            ascs[i] += sampler.calc_update(z[i], share[i], z[0], share[0])

        err = np.sum(np.abs(z - share))

        print(share, ascs, err)

    assert err < 0.12

if __name__ == "__main__":
    test_asc_sampler()