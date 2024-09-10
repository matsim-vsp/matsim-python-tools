""" Reference model to fine tune individal links. This model does not use features and is not trasferable to other scenarios. """

import jax.numpy as jnp

params = None

def batch_loss(params, inputs, targets):
    inputs = inputs.astype(int)

    # Select parameters by index
    preds = params[inputs].T

    # Calculate the loss
    error = jnp.sum((preds - targets) ** 2)

    return error
