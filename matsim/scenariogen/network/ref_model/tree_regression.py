""" Custom defined reference model for speed relative target """

# three level decision tree with regression at the leaf

# Inputs: length, (0)
# priority_lower, priority_equal, priority_higher,  (1,2,3)
# is_secondary_or_higher, is_primary_or_higher, is_motorway (4,5,6)
# speed (7)

params = [0.8, -0.1] * 21

def score(params, inputs):
    # lower prio
    if inputs[1] == 1:
        # highway
        if inputs[6] == 1:
            # >= 100kmh
            if inputs[7] >= 27.5:
                return params[0] + params[1] / inputs[0]
            else:
                return params[2] + params[3] / inputs[0]
        # primary
        elif inputs[5] == 1:
            return params[4] + params[5] / inputs[0]
        # secondary
        elif inputs[4] == 1:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[6] + params[7] / inputs[0]
            else:
                return params[8] + params[9] / inputs[0]
        else:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[10] + params[11] / inputs[0]
            else:
                return params[12] + params[13] / inputs[0]

    # equal prio
    elif inputs[2] == 1:
        # highway
        if inputs[6] == 1:
            # >= 100kmh
            if inputs[7] >= 27.5:
                return params[14] + params[15] / inputs[0]
            else:
                return params[16] + params[17] / inputs[0]
        # primary
        elif inputs[5] == 1:
            return params[18] + params[19] / inputs[0]
        # secondary
        elif inputs[4] == 1:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[20] + params[21] / inputs[0]
            else:
                return params[22] + params[23] / inputs[0]
        else:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[24] + params[25] / inputs[0]
            else:
                return params[26] + params[27] / inputs[0]

    # higher prio
    else:
        # highway
        if inputs[6] == 1:
            # >= 100kmh
            if inputs[7] >= 27.5:
                return params[28] + params[29] / inputs[0]
            else:
                return params[30] + params[31] / inputs[0]
        # primary
        elif inputs[5] == 1:
            return params[32] + params[33] / inputs[0]
        # secondary
        elif inputs[4] == 1:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[34] + params[35] / inputs[0]
            else:
                return params[36] + params[37] / inputs[0]
        else:
            # 30kmh or lower
            if inputs[7] <= 10:
                return params[38] + params[39] / inputs[0]
            else:
                return params[40] + params[41] / inputs[0]


def batch_loss(params, inputs, targets):
    error = 0
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
