# -*- coding: utf-8 -*-
"""PassiveAggressiveRegressor(C=0.015320363769859633, random_state=1373158606)
Error: 161.238227"""
def features(ft, data):
		data[0] = (ft.get("length") - 126.5781093424676) / 82.93604475431307
		data[1] = (ft.get("speed") - 8.347924642353416) / 0.2530674029724574
		data[2] = (ft.get("num_lanes") - 1.0161192826919203) / 0.1410293306032409
		data[3] = ft.get("change_speed")
		data[4] = ft.get("change_num_lanes")
		data[5] = ft.get("num_to_links")
		data[6] = ft.get("junction_inc_lanes")
		data[7] = ft.get("priority_lower")
		data[8] = ft.get("priority_equal")
		data[9] = ft.get("priority_higher")
		data[10] = ft.get("is_secondary_or_higher")
		data[11] = ft.get("is_primary_or_higher")
		data[12] = ft.get("is_motorway")
		data[13] = ft.get("is_link")

params = []
def score(params, inputs):
    return 820.7862981813687 + inputs[0] * -2.2407160935169324 + inputs[1] * -1.0312478382897772 + inputs[2] * -65.10322048874464 + inputs[3] * -3.7672954706609025 + inputs[4] * 91.56185003046016 + inputs[5] * 8.354883935056996 + inputs[6] * -16.573320689701585 + inputs[7] * 1.3872614339054785 + inputs[8] * 798.9462847274731 + inputs[9] * 20.45275201994965 + inputs[10] * 12.054157458777055 + inputs[11] * -11.583879746981143 + inputs[12] * -1.4911083760151145 + inputs[13] * 15.111478746337356

def batch_loss(params, inputs, targets):
    error = 0
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
