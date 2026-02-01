# -*- coding: utf-8 -*-

import numpy as np
from scipy.special import softmax

from matsim.calibration import ASCCalibrator

def lognormal(mu, sigma, size):
    s = np.sqrt(np.log(1 + (sigma / mu) ** 2))
    mean = np.log(mu) - s ** 2 / 2

    return np.random.lognormal(mean, s, size=(size,))


def target_share(dists, z_dist):
    """ Calculated the overall target share given the distance based shares and observed distances """
    lower_bound = 0

    total = np.zeros(4)
    for k, v in z_dist.items():
        trips = dists[(dists > lower_bound) & (dists <= k)]
        n = len(trips)

        lower_bound = k

        total += np.array(v) * n

    total /= np.sum(total)
    return total


def dist_share(probs, dists, z_dist):
    """ Expected share from obtained probabilities """

    result = {}
    lower_bound = 0
    for upper_bound in z_dist.keys():
        d = dists[:, 0]
        # probs only for distance group
        p = probs[(d > lower_bound) & (d <= upper_bound)]
        s = np.sum(p, axis=0)
        s /= s.sum(axis=0)

        result[upper_bound] = s
        lower_bound = upper_bound

    return result


def dist_err(share_dist, z_dist):
    err = {}
    for k, v in share_dist.items():
        err[k] = np.sum(np.abs(v - z_dist[k]))

    return err


def calc_median_dist(dists, z_dist):
    result = {}
    lower_bound = 0
    for k, v in z_dist.items():
        result[k] = np.median(dists[:, 0][(dists[:, 0] > lower_bound) & (dists[:, 0] <= k)])
        lower_bound = k

    return result


def test_algorithm():
    np.set_printoptions(precision=3, suppress=True)

    sampler = ASCCalibrator([], {}, {})

    np.random.seed(0)

    # Fixed utilities
    utils = np.random.rand(1000, 4)
    # Distance based costs
    costs = [0, 0.1, 0.05, 0.2]

    dists = lognormal(3000, 5000, size=1000)
    dists = np.tile(dists, (4, 1)).T

    ascs = np.zeros(4)

    # dist shares
    z_dist = {
        1500: [0.1, 0.5, 0.3, 0.1],
        4000: [0.2, 0.3, 0.1, 0.4],
        10000: [0.3, 0.2, 0.2, 0.3],
        np.inf: [0.4, 0.4, 0.1, 0.1],
    }

    # marginal utility per m for each mode
    utils_m = np.zeros((4, len(z_dist)))

    # deermin used idx for each group
    dist_idx = np.searchsorted(list(z_dist.keys()), dists[:,0])
    dist_idx = np.tile(dist_idx, (4, 1)).T


    median_dist = calc_median_dist(dists, z_dist)

    z = target_share(dists, z_dist)

    print("Target share", z)

    def choice(x_ascs, x_dist_utils):

        utils_for_group = np.take_along_axis(x_dist_utils, dist_idx, axis=0)
        dist_util = dists * costs * utils_for_group

        x = utils + x_ascs + dist_util + np.random.normal(size=(1000, 4))
        probs = softmax(x, axis=1)
        s = np.sum(probs, axis=0) / len(x)

        s_dist = dist_share(probs, dists, z_dist)

        return s, s_dist

    for it in range(50):

        share, share_dist = choice(ascs, utils_m)

        dist_errs = dist_err(share_dist, z_dist)

        for i in range(1, len(share)):
            ascs[i] += sampler.calc_asc_update(z[i], share[i], z[0], share[0])

            for j, (dist_group, v) in enumerate(z_dist.items()):
                # Real share in distance group
                z_i = z_dist[dist_group][i]
                z_0 = z_dist[dist_group][0]
                # Obtained share
                m_i = share_dist[dist_group][i]
                m_0 = share_dist[dist_group][0]

                update = sampler.calc_asc_update(z_i, m_i, z_0, m_0)

                utils_m[i, j] += update / median_dist[dist_group]

        err = np.sum(np.abs(z - share))

  #      print("ASCs", ascs, "Dist utils", utils_m)

    # This for playing around, not the same as the implemented algorithm
    print("Error", err)
    print("Share dist", share_dist, "Error", dist_errs)

