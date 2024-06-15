#!/usr/bin/env python

import random
from os import makedirs
from os.path import join

import optuna
import pandas as pd
import sklearn.ensemble
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold
from tqdm.auto import tqdm

from .models import create_regressor, model_to_java, model_to_py

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


class MLRegressor:
    """ General class for machine learning regression models """

    def __init__(self, n_trials=100, error="mae", fold=None, bounds=None):
        self.n_trials = n_trials
        self.fold = fold if fold else KFold(n_splits=5, shuffle=False)
        self.bounds = bounds
        self.error = mean_absolute_error
        self.models = {}
        self.df = None
        self.exclude = None
        self.target = None
        self.pb: tqdm = None
        self.best = None
        # Currently trained model
        self.model = None

    def get(self, idx):
        tf = self.df if idx is None else self.df.iloc[idx]
        return tf.drop(columns=self.exclude + [self.target]), tf[self.target].to_numpy()

    def best_model(self, models):
        errors = []
        for m in models:
            X, y = self.get(None)
            X = self.scaler.transform(X)

            pred = m.predict(X)
            err = self.error(y, pred)

            errors.append((m, err))

        errors = sorted(errors, key=lambda m: m[1])

        return errors[0]

    def callback(self, study: optuna.Study, trial: optuna.Trial):
        """ Callback during training """
        if study.best_trial == trial:
            self.best = self.model
            self.pb.set_postfix({"error": trial.values[0], "iter": trial.number})

        self.pb.update(1)

    def fit(self, df: pd.DataFrame, target: str,
            exclude: list[str] = None,
            normalize: list[str] = None):
        """ Fit model to the data

        :param df: DataFrame with the data
        :param target: Column name of target values contained in df
        :param exclude: List of columns to exclude from the model
        :param normalize: List of columns to normalize
        """
        self.df = df
        self.exclude = [] if exclude is None else exclude
        self.target = target

        _scaler = sklearn.preprocessing.StandardScaler(with_mean=True)

        if normalize is None:
            normalize = []

        self.scaler = sklearn.compose.ColumnTransformer([
            ("scale", _scaler, [df.columns.get_loc(x) for x in normalize])  # column indices
        ],
            remainder="passthrough"
        )

        # Fit scaler, excluding target column
        self.scaler.fit(self.get(None)[0])

        def objective(classifier_name):
            def _fn(trial):
                r = random.Random(42)

                random_state = r.getrandbits(31)

                seq = iter(self.fold.split(df))

                error = 0
                i = 0

                candidates = []

                for train, test in seq:
                    model = create_regressor(trial, classifier_name, random_state)

                    candidates.append(model)

                    X, y = self.get(train)
                    X = self.scaler.transform(X)

                    model.fit(X, y)

                    Xval, yval = self.get(test)
                    Xval = self.scaler.transform(Xval)

                    pred = model.predict(Xval)

                    error += self.error(yval, pred)
                    i += 1

                self.model = self.best_model(candidates)[0]

                return error / i

            return _fn

        self.models = {}

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        with tqdm(total=len(classifier), position=0, leave=True) as pbar:
            for m in classifier:
                pbar.set_description(f"Training model {m}")

                with tqdm(total=self.n_trials, desc="Iteration", position=1, leave=True) as self.pb:
                    study = optuna.create_study(sampler=optuna.samplers.TPESampler(seed=42), direction='minimize')
                    study.optimize(objective(m), n_trials=self.n_trials, callbacks=[self.callback],
                                   show_progress_bar=False)

                    self.models[m] = self.best

                pbar.update(1)

        self.best = self.best_model(self.models.values())

    def write_java(self, folder, package_name, class_name):
        """ Write trained models as java code"""

        if self.best is None:
            raise ValueError("No model trained")

        output = join(folder, package_name.replace(".", "/"))
        makedirs(output, exist_ok=True)

        with open(join(output, class_name + ".java"), "w") as f:
            code = model_to_java(class_name, package_name, self.best, self.scaler, self.bounds, self.get(None)[0])
            f.write(code)

    def write_python(self, folder, name):
        """ Write trained models as python code"""

        if self.best is None:
            raise ValueError("No model trained")

        makedirs(folder, exist_ok=True)

        with open(join(folder, "__init__.py"), "w") as f:
            f.write("")

        with open(join(folder, name + ".py"), "w") as f:

            # TODO: bounds not implemented

            code = model_to_py(name, self.best, self.scaler, self.get(None)[0])
            f.write("# -*- coding: utf-8 -*-\n")
            f.write("\"\"\"%s\nError: %f\"\"\"\n" % self.best)
            f.write(code)
