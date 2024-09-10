#!/usr/bin/env python

import argparse
import json
import os
import time
from dataclasses import dataclass
from functools import reduce
from random import Random

import numpy as np
import jax.numpy as jnp
import optax
from jax import grad, random
from requests import post
from tqdm import trange

URL = "http://localhost:%d"

METADATA = "network-opt-freespeed", "Optimize parameters for free-speed model. Server must be running before starting."


def as_list(array):
    return [float(x) for x in array]


def req(port, priority, rbl, traffic_light):
    req = {
        "priority": as_list(priority),
        "right_before_left": as_list(rbl),
        "traffic_light": as_list(traffic_light),
    }

    results = [post(URL % p, json=req).json() for p in port]

    data = {}
    for k in results[0]["data"].keys():
        data[k] = reduce(lambda x, y: x + y, [d["data"][k] for d in results])

    res = {
        "rmse": np.mean([x["rmse"] for x in results]),
        "mae": np.mean([x["mae"] for x in results]),
        "data": data
    }

    return req, res


@dataclass
class Model:
    name: str
    module: object
    optimizer: optax.adam
    opt_state: object
    params: jnp.array
    loss: callable


def setup(parser: argparse.ArgumentParser):
    parser.add_argument("--steps", type=int, help="Number of training steps", default=1500)
    parser.add_argument("--resume", help="File with parameters to to resume", default=None)
    parser.add_argument("--port", type=int, nargs="+", help="Port to connect on", default=[9090])
    parser.add_argument("--ref-model", required=False, default=None,
                        help="Use an integrated model instead of importing", choices=["tree", "individual", "germany"])
    parser.add_argument("--ref-size", type=int, help="Number of links (needed for individual model)", default=0)
    parser.add_argument("--learning-rate", type=float, help="Start learning rate", default=1e-4)
    parser.add_argument("--batch-size", type=int, help="Batch size", default=128)
    parse.add_argument("--sample-unique", help="Every batch element is a different element", action="store_true", default=False)
    parser.add_argument("--output", help="Output folder for params", default="output-params")


def main(args):
    batch_size = args.batch_size
    batches = 5

    models = {}
    resume = {}

    if args.ref_model == "tree":
        from .ref_model import tree as p
        rbl = tl = p
    elif args.ref_model == "individual":
        # Enables non relative import as well
        try:
            from .ref_model import individual as p
            rbl = tl = p
        except ImportError:
            from ref_model import individual as p
            rbl = tl = p

    elif args.ref_model == "germany":
        from .ref_model.germany import speedRelative_priority as p
        from .ref_model.germany import speedRelative_right_before_left as rbl
        from .ref_model.germany import speedRelative_traffic_light as tl
    else:
        # Import model, must be present on path
        from gen_code import speedRelative_priority as p
        from gen_code import speedRelative_right_before_left as rbl
        from gen_code import speedRelative_traffic_light as tl

    if args.resume:
        print("Resuming from", args.resume)
        with open(args.resume) as f:
            resume = json.load(f)

    for (module, name) in ((p, "priority"), (tl, "traffic_light"), (rbl, "right_before_left")):
        schedule = optax.exponential_decay(
            init_value=args.learning_rate, decay_rate=0.9,
            # Every 5% steps, decay 0.9
            transition_steps=int(batches * args.steps / 20), transition_begin=int(0.35 * args.steps * batches),
            staircase=False
        )

        # Need to load default params statically
        if module.params is None:
            params = jnp.array(resume[name]) if name in resume else jnp.ones(args.ref_size) * 0.85
        else:
            params = jnp.array(resume[name] if name in resume else module.params)

        optimizer = optax.adam(schedule)
        opt_state = optimizer.init(params)

        models[name] = Model(
            name, module, optimizer, opt_state, params, grad(module.batch_loss)
        )

    r = Random(42)

    out = os.path.join(args.output, time.strftime("%Y%m%d-%H%M"))
    os.makedirs(out, exist_ok=True)

    print("Writing to", out)

    with trange(args.steps) as outer:

        # A simple update loop.
        for i in outer:
            params, result = req(args.port, models["priority"].params,
                                 models["right_before_left"].params, models["traffic_light"].params)

            name = "it%04d_mae_%.3f_rmse_%.3f.json" % (i, result["mae"], result["rmse"])

            with open(os.path.join(out, name), "w") as f:
                json.dump(params, f)

            outer.set_postfix(mae=result["mae"], rmse=result["rmse"])
            data = result["data"]

            for k, m in models.items():

                xs = [d["x"] for d in data[k]]
                xs = jnp.array(xs)

                ys = [d["yTrue"] for d in data[k]]
                ys = jnp.array(ys)

                for j in range(batches):
                    key = random.PRNGKey(r.getrandbits(31))

                    idx = random.choice(key, jnp.arange(0, xs.shape[0]), replace=not args.sample_unique, shape=(batch_size,))

                    grads = m.loss(m.params, xs[idx], ys[idx])

                    updates, m.opt_state = m.optimizer.update(grads, m.opt_state)
                    m.params = optax.apply_updates(m.params, updates)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog=METADATA[0], description=METADATA[1])
    setup(parser)
    main(parser.parse_args())
