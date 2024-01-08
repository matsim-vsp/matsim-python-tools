import numpy as np

from matsim.calibration import ASCCalibrator


def test_asc_sampler():
    # variables are not needed for this test
    sampler = ASCCalibrator([], {}, {})

    np.random.seed(0)

    utils = np.random.rand(1000, 4)
    ascs = np.zeros(4)

    # real shares (target)
    z = [0.1, 0.5, 0.3, 0.1]

    for it in range(200):

        modes = np.argmax(utils + ascs + np.random.normal(size=(1000, 4)), axis=1)
        _, counts = np.unique(modes, return_counts=True)

        share = counts / np.sum(counts)

        for i in range(1, len(share)):
            ascs[i] += sampler.calc_asc_update(z[i], share[i], z[0], share[0])

        err = np.sum(np.abs(z - share))

        print(share, ascs, err)

    assert err < 0.12


if __name__ == "__main__":
    test_asc_sampler()
