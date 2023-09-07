""" Custom defined reference model for speed relative target """

# simple decision tree

# Inputs: length, (0)
# priority_lower, priority_equal, priority_higher,  (1,2,3)
# is_secondary_or_higher, is_primary_or_higher, is_motorway (4,5,6)
# speed (7)

params = [0.9, 0.8, 0.9, 0.8, 0.7, 0.7, 0.7, 0.7] * 3

def score(params, inputs):
    # lower prio
    if inputs[1] == 1:
        # highway
        if inputs[6] == 1:
            # >= 100kmh
            if inputs[7] >= 27.5:
                return params[0]
            else:
                return params[1]
        # primary
        elif inputs[5] == 1:
            # >= 80khm
            if inputs[7] >= 22:
                return params[2]
            else:
                return params[3]
        # secondary
        elif inputs[4] == 1:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[4]
            else:
                return params[5]
        else:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[6]
            else:
                return params[7]

    # equal prio
    elif inputs[2] == 1:
        # highway
        if inputs[6] == 1:
            # >= 100kmh
            if inputs[7] >= 27.5:
                return params[8]
            else:
                return params[9]
        # primary
        elif inputs[5] == 1:
            # >= 80khm
            if inputs[7] >= 22:
                return params[10]
            else:
                return params[11]
        # secondary
        elif inputs[4] == 1:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[12]
            else:
                return params[13]
        else:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[14]
            else:
                return params[15]

    # higher prio
    else:
        # highway
        if inputs[6] == 1:
            # >= 100kmh
            if inputs[7] >= 27.5:
                return params[16]
            else:
                return params[17]
        # primary
        elif inputs[5] == 1:
            # >= 80khm
            if inputs[7] >= 22:
                return params[18]
            else:
                return params[19]
        # secondary
        elif inputs[4] == 1:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[20]
            else:
                return params[21]
        else:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[22]
            else:
                return params[23]


def batch_loss(params, inputs, targets):
    error = 0
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
