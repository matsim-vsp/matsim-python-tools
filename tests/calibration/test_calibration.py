# -*- coding: utf-8 -*-

import numpy as np

from scipy.special import softmax

from matsim.calibration import ASCCalibrator


def test_asc_sampler():
    # variables are not needed for this test
    sampler = ASCCalibrator([], {}, {})

    np.random.seed(0)

    utils = np.random.rand(1000, 4)
    ascs = np.zeros(4)

    # real shares (target)
    z = [0.1, 0.5, 0.3, 0.1]

    def argmax(x):
        modes = np.argmax(utils + x + np.random.normal(size=(1000, 4)), axis=1)
        _, counts = np.unique(modes, return_counts=True)
        s = counts / np.sum(counts)
        return s

    def soft_max(x):
        x = utils + x + np.random.normal(size=(1000, 4))

        probs = softmax(x, axis=1)
        s = np.sum(probs, axis=0) / len(x)
        return s

    for it in range(50):

        share = soft_max(ascs)

        for i in range(1, len(share)):
            ascs[i] += sampler.calc_asc_update(z[i], share[i], z[0], share[0])

        err = np.sum(np.abs(z - share))

        print("ASCs", ascs)

    err = 0

    for i in range(5):
        share = soft_max(ascs)
        err += np.sum(np.abs(z - share)) / 5

        print("Share", share)

    print("Error", err)

    assert err < 0.03


if __name__ == "__main__":
    test_asc_sampler()
