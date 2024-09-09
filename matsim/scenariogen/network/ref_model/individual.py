""" Reference model to fine tune individal links. This model does not use features and is not trasferable to other scenarios. """

# Each link has its own target speed


params = None

def score(params, inputs):
    return params[inputs[0]]


def batch_loss(params, inputs, targets):
    error = 0
    inputs = inputs.astype(int)
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
