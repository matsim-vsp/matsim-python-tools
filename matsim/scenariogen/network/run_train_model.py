#!/usr/bin/env python

import random
from argparse import ArgumentParser
from os import makedirs
from os.path import join

import optuna
import sklearn.ensemble
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold

from .features import build_datasets
from .models import create_regressor, model_to_java, model_to_py

METADATA = "network-train-model", "Train models for network capacity and freeflow speed."


def setup(parser: ArgumentParser):
    parser.add_argument("--network-features", help="Path to file with edge features", required=True)
    parser.add_argument("--input-intersection", help="Path to file with intersection results")
    parser.add_argument("--input-routes", help="Path to file with route results.")


def main(args):
    dfs = build_datasets(args.network_features, args.input_intersection, args.input_routes)
    targets = dfs.keys()

    def get(idx, t):
        if idx is not None:
            df = dfs[t].iloc[idx]
        else:
            df = dfs[t]

        return df.drop(columns=["target"]), df.target.to_numpy()

    scaler = {}

    for t in targets:
        _scaler = sklearn.preprocessing.StandardScaler(with_mean=True)

        df = get(None, t)[0]

        norm = ["length", "speed", "numFoes", "numLanes", "junctionSize"]

        scaler[t] = sklearn.compose.ColumnTransformer([
            ("scale", _scaler, [df.columns.get_loc(x) for x in norm])  # column indices
        ],
            remainder="passthrough"
        )

        scaler[t].fit(df)

    print("Model targets", targets)

    # %%

    def best_model(ms, t):
        errors = []
        for m in ms:
            X, y = get(None, t)
            X = scaler[t].transform(X)

            pred = m.predict(X)
            err = mean_absolute_error(y, pred)

            errors.append((m, err))

        errors = sorted(errors, key=lambda m: m[1])

        return errors[0]

    fold = KFold(n_splits=6, shuffle=True)
    n_trials = 150

    classifier = {
        'mean',
        'XGBRFRegressor',
        'XGBRegressor',
        'RandomForestRegressor',
        'ExtraTreesRegressor',
        'LGBMRegressor',
        'DecisionTreeRegressor',
        'PassiveAggressiveRegressor',
        # More
        #   'SVR',
        #   'KernelSVC',
        #   'QLatticeRegressor',
        #   'LinearSVR',
        #   'Ridge',
        #   'SGDRegressor',
        #   'LogisticRegression',
        #   'AdaGradRegressor',
        #   'CDRegressor',
        #   'FistaRegressor',
        #   'SDCARegressor',
        #   'Lasso',
        #   'ElasticNet'
    }

    def objective(classifier_name, target):
        global model

        def _fn(trial):
            global model

            r = random.Random(42)

            random_state = r.getrandbits(31)

            seq = iter(fold.split(dfs[target]))

            error = 0
            i = 0

            candidates = []

            for train, test in seq:
                model = create_regressor(trial, classifier_name, random_state)

                candidates.append(model)

                X, y = get(train, target)
                X = scaler[t].transform(X)

                model.fit(X, y)

                Xval, yval = get(test, target)
                Xval = scaler[t].transform(Xval)

                pred = model.predict(Xval)

                error += mean_absolute_error(yval, pred)

                i += 1

            best = best_model(candidates, t)[0]

            return error / i

        return _fn

    def callback(study, trial):
        global best
        global model
        if study.best_trial == trial:
            best = model

    models = {}
    for t in targets:

        print("Training", t)

        models[t] = {}

        for m in classifier:
            print("Running model", m)

            study = optuna.create_study(sampler=optuna.samplers.TPESampler(seed=42), direction='minimize')
            study.optimize(objective(m, t), n_trials=n_trials, callbacks=[callback], show_progress_bar=True)

            models[t][m] = best

    for t in targets:
        print("#### ", t)

        m = best_model(models[t].values(), t)

        print("Best model", m)

        makedirs("gen_code", exist_ok=True)

        with open(join("gen_code", "__init__.py"), "w") as f:
            f.write("")

        with open(join("gen_code", t.capitalize() + ".java"), "w") as f:
            code = model_to_java(t, m[0], scaler[t], get(None, t)[0])
            f.write(code)

        with open(join("gen_code", t + ".py"), "w") as f:
            code = model_to_py(t, m[0], scaler[t], get(None, t)[0])
            f.write("# -*- coding: utf-8 -*-\n")
            f.write(code)


if __name__ == "__main__":
    parser = ArgumentParser(prog=METADATA[0], description=METADATA[1])
    setup(parser)
    main(parser.parse_args())
