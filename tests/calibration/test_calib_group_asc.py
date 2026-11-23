# -*- coding: utf-8 -*-

import optuna
import pandas as pd
import pytest

from matsim.calibration import ASCGroupCalibrator

modes = ["walk", "car", "pt"]


def subpop_target():
    return pd.DataFrame({
        "subpopulation": [1, 1, 1, 2, 2, 2],
        "mode": modes * 2,
        "share": [0.3, 0.4, 0.3, 0.5, 0.2, 0.3]
    })


def test_subpopulation_validation():
    with pytest.raises(ValueError, match="calib_base"):
        ASCGroupCalibrator(modes, {}, subpop_target(), config_format="subpopulation")

    target = subpop_target().rename(columns={"subpopulation": "age"})
    with pytest.raises(ValueError, match="exactly one group"):
        ASCGroupCalibrator(modes, {}, target, calib_base="never", config_format="subpopulation")


def create_trial(calib):
    study = optuna.create_study()
    trial = study.ask({
        "asc-[subpopulation=%s]-%s" % (s, m): optuna.distributions.FloatDistribution(-10, 10)
        for s in ("1", "2") for m in modes
    })

    trial.suggest_float = lambda name, *args: -1.0 if name.endswith("car") else (0.0 if name.endswith("walk") else -2.0)

    return study, trial


def test_subpopulation_config():
    initial = pd.DataFrame({
        "subpopulation": [1, None],
        "mode": ["car", "pt"],
        "value": [-1.5, -0.5]
    })

    calib = ASCGroupCalibrator(modes, initial, subpop_target(), calib_base="never",
                               config_format="subpopulation", config_output="yaml")

    assert calib.num_targets == 6

    assert calib.sample_initial("[subpopulation=1]-car") == -1.5
    # Fallback to value without group
    assert calib.sample_initial("[subpopulation=1]-pt") == -0.5
    assert calib.sample_initial("[subpopulation=2]-car") == 0

    study, trial = create_trial(calib)

    config = {}
    calib.update_config(study, trial, "asc-", config)
    assert calib.update_args(study, trial, "asc-") == []

    params = config["scoring"]["scoringParameters"]
    assert [list(p.keys())[0] for p in params] == ["subpopulation", "subpopulation"]
    assert sorted(p["subpopulation"] for p in params) == ["1", "2"]

    for p in params:
        # Fixed mode with 0 is not written
        assert p["modeParams"] == [{"mode": "car", "constant": -1.0}, {"mode": "pt", "constant": -2.0}]


def test_subpopulation_cli():
    calib = ASCGroupCalibrator(modes, {}, subpop_target(), calib_base="never", config_format="subpopulation")

    study, trial = create_trial(calib)

    config = {}
    calib.update_config(study, trial, "asc-", config)
    assert config == {}

    assert calib.update_args(study, trial, "asc-") == [
        "--config:scoring.scoringParameters[subpopulation=%s].modeParams[mode=%s].constant=%s" % (s, m, c)
        for s in ("1", "2") for m, c in (("car", -1.0), ("pt", -2.0))
    ]

    with pytest.raises(ValueError, match="cli"):
        ASCGroupCalibrator(modes, {}, subpop_target(), calib_base="never", config_format="sbb", config_output="cli")
