#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import re
from time import time

import numpy as np
import pandas as pd
import sklearn
import sklearn.compose
import sklearn.ensemble
import sklearn.linear_model
import sklearn.svm
from sklearn.base import BaseEstimator, RegressorMixin, ClassifierMixin
from sklearn.metrics import mean_squared_error

try:
    import lightning.regression
    import lightning.classification
except ValueError as e:
    print("Error during lightning import", e)

try:
    import feyn
except ImportError as e:
    print("Error importing feyn")


import xgboost as xgb
import lightgbm as lgb

from sympy.utilities.codegen import codegen


def powerset(iterable):
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s) + 1))


class QLatticeBase(BaseEstimator):
    _kind = None
    _loss = None

    @staticmethod
    def as_df(X, y=None):
        tf = pd.DataFrame(X, dtype=np.float64)
        if y is not None:
            tf["y"] = y

        tf.columns = tf.columns.map(lambda x: "data%s" % x if x != "y" else "y")

        return tf

    def __init__(self, max_complexity, n_epochs, criterion, progress, random_state) -> None:
        super().__init__()

        self.ql = feyn.QLattice(random_state)
        self.n_epochs = n_epochs
        self.max_complexity = max_complexity
        self.criterion = criterion
        self.progress = progress
        self.random_state = random_state

    def fit(self, X, y, sample_weight=None, test=None, val=None, f=None, ftest=None, fval=None, val_interval=10):

        tf = self.as_df(X, y)

        if test is not None:
            test = self.as_df(*test)

        if val is not None:
            val = self.as_df(*val)

        models = []
        m_count = 0

        start = time()
        for i in range(1, self.n_epochs + 1):

            new_sample = self.ql.sample_models(
                input_names=tf.columns,
                output_name='y',
                kind=self._kind,
                max_complexity=self.max_complexity
            )

            models += new_sample
            m_count += len(new_sample)

            models = feyn.fit_models(
                models=models,
                data=tf,
                sample_weights=sample_weight,
                loss_function=self._loss,
                criterion=self.criterion,
                threads=8
            )

            # Sort for val method for pruning
            if test is not None:
                if f is None:
                    f = lambda pred: mean_squared_error(tf["y"], pred)

                if ftest is None:
                    ftest = lambda pred: mean_squared_error(test["y"], pred)

                if fval is None:
                    fval = lambda pred: mean_squared_error(val["y"], pred)

                # Custom prune / sorting
                if val is not None and ((i - 1) % val_interval == 0 or i == self.n_epochs):
                    models = list(sorted(
                        models, key=lambda m: ftest(m.predict(test)) + fval(m.predict(val))
                    ))
                else:
                    models = list(sorted(
                        models, key=lambda m: f(m.predict(tf)) + ftest(m.predict(test))
                    ))

            models = feyn.prune_models(models)

            info = ""
            if ftest is not None:
                # Custom label
                info += " Test: %.2f" % ftest(models[0].predict(test))

            if val is not None and fval is not None:
                # Custom label
                info += " Val: %.2f" % fval(models[0].predict(val))

            elapsed = time() - start
            if len(models) > 0 and self.progress:
                feyn.show_model(
                    models[0],
                    feyn.tools.get_progress_label(i, self.n_epochs, elapsed, m_count) + info,
                    update_display=True,
                )

            self.ql.update(models)

        self.best = [models[0]] + feyn.get_diverse_models(models[1:], n=5)

        return self

    def predict(self, X):
        return self.best[0].predict(self.as_df(X))

    def show(self):
        feyn.show_model(self.best[0])

    def sympify(self):
        return self.best[0].sympify(signif=9, symbolic_lr=True, include_weights=True)

    def plot(self, X, y, Xval, yval):

        train = self.as_df(X, y)
        test = self.as_df(Xval, yval)

        self.best[0].plot(
            data=train,
            compare_data=test
        )


class QLatticeClassifier(QLatticeBase, ClassifierMixin):

    def __init__(self, max_complexity=10, n_epochs=30, criterion="bic", progress=False, random_state=-1) -> None:
        super().__init__(max_complexity, n_epochs, criterion, progress, random_state)

        self._kind = "classification"
        self._loss = "binary_cross_entropy"

    def copy(self, n=0):
        """ Make new model by copying the best n"""

        other = QLatticeClassifier(self.max_complexity, self.n_epochs, self.progress, self.random_state)
        other.best = [self.best[n]]

        return other


class QLatticeRegressor(QLatticeBase, RegressorMixin):

    def __init__(self, max_complexity=10, n_epochs=30, criterion="bic", progress=False, random_state=-1) -> None:
        super().__init__(max_complexity, n_epochs, criterion, progress, random_state)

        self._kind = "regression"
        self._loss = "squared_error"

    def copy(self, n=0):
        """ Make new model by copying the best n"""

        other = QLatticeRegressor(self.max_complexity, self.n_epochs, self.progress, self.random_state)
        other.best = [self.best[n]]

        return other


def create_regressor(trial, classifier_name, random_state):
    """ Create regressor model from given classifier """

    if classifier_name == 'mean':
        model = sklearn.dummy.DummyRegressor()

    elif classifier_name == 'SVR':
        kernel = trial.suggest_categorical('kernel', ['linear', 'poly', 'rbf', 'sigmoid'])
        svc_c = trial.suggest_float('svc_r', 1e-10, 1e10, log=True)
        model = sklearn.svm.SVR(C=svc_c, gamma='auto', kernel=kernel)

    elif classifier_name == 'QLatticeRegressor':

        model = QLatticeRegressor(trial.suggest_int('complexity', 3, 6, step=1), random_state=random_state)

    elif classifier_name == 'RandomForestRegressor':
        rf_max_depth = trial.suggest_int('rf_max_depth', 2, 4)
        rf_n = trial.suggest_int('rf_n', 5, 30, step=5)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 8, step=1)
        b = trial.suggest_categorical('bootstrap', [True, False])

        model = sklearn.ensemble.RandomForestRegressor(max_depth=rf_max_depth, n_estimators=rf_n,
                                                       oob_score=b, min_samples_split=min_samples_split,
                                                       random_state=random_state)
    elif classifier_name == 'XGBRFRegressor':

        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'mae',
            'max_depth': trial.suggest_int('max_depth', low=2, high=4),
            'min_child_weight': trial.suggest_int('min_child_weight', low=1, high=10),
            'eta': trial.suggest_float('eta', 0.01, 1, log=True),
            'lambda': trial.suggest_float('lambda', 0.01, 1, log=True),
            'alpha': trial.suggest_float('alpha', 0.01, 1, log=True),
            'gamma': trial.suggest_float('gamma', 0.01, 1, log=True),
            'n_estimators': trial.suggest_int('rf_n', 5, 30, step=5),
            'subsample': 0.9,
            'colsample_bytree': 0.9,
            'colsample_bynode': 0.9,
            'random_state': random_state
        }

        model = xgb.XGBRFRegressor(**params)

    elif classifier_name == 'XGBRegressor':

        params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'mae',
            'max_depth': trial.suggest_int('max_depth', low=2, high=4),
            'min_child_weight': trial.suggest_int('min_child_weight', low=1, high=10),
            'eta': trial.suggest_float('eta', 0.01, 1, log=True),
            'lambda': trial.suggest_float('lambda', 0.01, 1, log=True),
            'alpha': trial.suggest_float('alpha', 0.01, 1, log=True),
            'gamma': trial.suggest_float('gamma', 0.01, 1, log=True),
            'n_estimators': trial.suggest_int('rf_n', 5, 30, step=5),
            'subsample': 0.9,
            'colsample_bytree': 0.9,
            'colsample_bynode': 0.9,
            'random_state': random_state
        }

        model = xgb.XGBRegressor(**params)

    elif classifier_name == 'ExtraTreesRegressor':

        rf_n = trial.suggest_int('rf_n', 5, 30, step=5)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 8, step=1)
        max_depth = trial.suggest_int('max_depth', 2, 4)
        b = trial.suggest_categorical('bootstrap', [True, False])

        model = sklearn.ensemble.ExtraTreesRegressor(n_estimators=rf_n,
                                                     min_samples_split=min_samples_split,
                                                     max_depth=max_depth,
                                                     bootstrap=b, oob_score=b,
                                                     random_state=random_state)

    elif classifier_name == 'LGBMRegressor':

        params = {
            'objective': 'regression',
            'num_leaves': trial.suggest_int('num_leaves', 2, 32, log=True),
            'n_estimators': trial.suggest_int('n_estimators', 5, 30, step=5),
            #  'min_child_weight': trial.suggest_loguniform('min_child_weight', 0.0001, 1),
            #  'min_child_samples': trial.suggest_int('min_child_samples', low=5, high=30, step=5),
            'subsample': 0.9,
            'subsample_freq': 10,
            'colsample_bytree': 0.9,
            'reg_alpha': trial.suggest_float('alpha', 1e-10, 1, log=True),
            'random_state': random_state
        }

        model = lgb.LGBMRegressor(**params)

    elif classifier_name == "DecisionTreeRegressor":

        min_samples_split = trial.suggest_int('min_samples_split', 2, 8, step=1)
        max_depth = trial.suggest_int('max_depth', 2, 4)

        model = sklearn.tree.DecisionTreeRegressor(max_depth=max_depth, min_samples_split=min_samples_split,
                                                   random_state=random_state)


    elif classifier_name == "BaggingRegressor":

        reg = sklearn.linear_model.PassiveAggressiveRegressor(C=trial.suggest_float('C', 0.0001, 100, log=True))
        model = sklearn.ensemble.BaggingRegressor(reg,
                                                  n_estimators=trial.suggest_int('rf_n', 5, 30, step=5),
                                                  max_samples=trial.suggest_float('alpha', 0.2, 1),
                                                  random_state=random_state)

    elif classifier_name == 'Ridge':

        model = sklearn.linear_model.Ridge(alpha=trial.suggest_float('alpha', 0.001, 1000, log=True), solver='saga',
                                           random_state=random_state)

    elif classifier_name == 'Lasso':

        model = sklearn.linear_model.Lasso(alpha=trial.suggest_float('alpha', 0.001, 1000, log=True),
                                           random_state=random_state)


    elif classifier_name == 'ElasticNet':

        model = sklearn.linear_model.ElasticNet(alpha=trial.suggest_float('alpha', 0.01, 1, log=True),
                                                l1_ratio=trial.suggest_float('ratio', 0, 1),
                                                random_state=random_state)
    elif classifier_name == 'SGDRegressor':

        model = sklearn.linear_model.SGDRegressor(alpha=trial.suggest_float('alpha', 0.0001, 1, log=True),
                                                  random_state=random_state)

    elif classifier_name == "LinearSVR":

        model = sklearn.svm.LinearSVR(C=trial.suggest_float('C', 0.001, 1000, log=True), dual=False, max_iter=2000,
                                      loss="squared_epsilon_insensitive", random_state=random_state)

    elif classifier_name == 'PassiveAggressiveRegressor':

        model = sklearn.linear_model.PassiveAggressiveRegressor(C=trial.suggest_float('C', 0.0001, 100, log=True),
                                                                random_state=random_state)

    elif classifier_name == 'LogisticRegression':

        model = sklearn.linear_model.LogisticRegression(C=trial.suggest_float('C', 0.0001, 100, log=True),
                                                        solver='saga', random_state=random_state)

    elif classifier_name == 'AdaGradRegressor':

        model = lightning.regression.AdaGradRegressor(eta=trial.suggest_float('eta', 0.0001, 10, log=True),
                                                      alpha=trial.suggest_float('alpha', 0.0001, 10, log=True),
                                                      random_state=random_state)

    elif classifier_name == 'CDClassifier':

        model = lightning.regression.CDClassifier(C=trial.suggest_float('C', 0.0001, 10, log=True),
                                                  alpha=trial.suggest_float('alpha', 0.0001, 10, log=True),
                                                  random_state=random_state)

    elif classifier_name == 'FistaClassifier':

        model = lightning.regression.FistaClassifier(C=trial.suggest_float('C', 0.0001, 10, log=True),
                                                     alpha=trial.suggest_float('alpha', 0.0001, 10, log=True),
                                                     random_state=random_state)

    elif classifier_name == 'SDCAClassifier':

        model = lightning.regression.SDCAClassifier(alpha=trial.suggest_float('alpha', 0.0001, 10, log=True),
                                                    random_state=random_state)

    elif classifier_name == 'OneClassSVM':

        kernel = trial.suggest_categorical('kernel', ['linear', 'poly', 'rbf', 'sigmoid'])
        gamma = trial.suggest_categorical('gamma', ['scale', 'auto'])
        nu = trial.suggest_float('nu', 0, 1)

        model = sklearn.svm.OneClassSVM(kernel=kernel, gamma=gamma, nu=nu, random_state=random_state)

    elif classifier_name == 'KernelSVC':

        kernel = trial.suggest_categorical('kernel', ['linear', 'poly', 'rbf', 'sigmoid', 'cosine'])
        model = lightning.regression.KernelSVC(alpha=trial.suggest_float('alpha', 0.0001, 10, log=True),
                                               kernel=kernel, random_state=random_state)

    else:
        raise Exception("Unknown regressor: " + classifier_name)

    return model


def sympy_to_c(model):
    # classifier can also be used directly if only 2 classes
    [(c_name, c_code), (h_name, c_header)] = codegen(("score", model.sympify()), "C89", "model", header=False,
                                                     empty=False)
    c_code = re.sub(r"data([0-9]+)", r"data[\1]", c_code)

    return c_code


def model_to_java(name, model, scaler, df):
    """ Convert to java source file """
    import m2cgen as m2c

    name = name.capitalize()

    code = m2c.export_to_java(model, "org.matsim.prepare.network", name)

    code, params = replace_params(code)

    imp = """import it.unimi.dsi.fastutil.objects.Object2DoubleMap;
    
/**
* Generated model, do not modify.
*/
public final class"""

    code = code.replace("public class", imp)
    code = code.replace(name, name + " implements FeatureRegressor")

    features = [f"data[{i}] = {s};\n" for i, s in enumerate(model_features(scaler, df))]

    idx = code.index("public static double score")

    pre = """
    public static %s INSTANCE = new %s();
    public static final double[] DEFAULT_PARAMS = %s;

    @Override
    public double predict(Object2DoubleMap<String> ft) {
        return predict(ft, DEFAULT_PARAMS);
    }
    
    @Override
    public double[] getData(Object2DoubleMap<String> ft) {
        double[] data = new double[%d];
""" % (name, name, str(params).replace("[", "{").replace("]", "}"), len(features))

    for ft in features:
        pre += "\t\t" + ft

    pre += """
        return data;
    }
    
    @Override
    public double predict(Object2DoubleMap<String> ft, double[] params) {

        double[] data = getData(ft);
        for (int i = 0; i < data.length; i++)
            if (Double.isNaN(data[i])) throw new IllegalArgumentException("Invalid data at index: " + i);
    
        return score(data, params);
    }
    """

    code = code.replace("score(double[] input)", "score(double[] input, double[] params)")

    return f"{code[:idx]}{pre}{code[idx:]}"


def model_to_py(name, model, scaler, df):
    import m2cgen as m2c

    code = m2c.export_to_python(model, function_name="score")

    code, params = replace_params(code)

    code = code.replace("input", "inputs")
    code = code.replace("(inputs):", "(params, inputs):")

    features = "\t\t".join([f"data[{i}] = {s}\n" for i, s in enumerate(model_features(scaler, df))])
    features = features.replace(".getDouble(", ".get(")

    code = """def features(ft, data):
\t\t%s
params = %s
""" % (features, params) + code

    code += """
def batch_loss(params, inputs, targets):
    error = 0
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
"""

    return code


def replace_params(code):
    """ Replaces and collects model parameters """

    pattern = re.compile(r"(var\d+) = (-?\d+.\d+)")

    params = []
    new_code = ''
    start = 0

    for m in pattern.finditer(code):
        end, newstart = m.span()
        new_code += code[start:end]
        rep = "%s = params[%d]" % (m.group(1), len(params))
        new_code += rep
        start = newstart

        params.append(float(m.group(2)))

    new_code += code[start:]

    return new_code, params


def model_features(scaler, df):
    for name, t, ids in scaler.transformers_:

        for i, idx in enumerate(ids):

            c = df.columns[idx]

            if name == "scale":

                t = scaler.named_transformers_[name]

                with_mean = t.get_params()["with_mean"]

                if with_mean:
                    yield f"(ft.getDouble(\"{c}\") - {t.mean_[i]}) / {t.scale_[i]}"
                else:
                    yield f"ft.getDouble(\"{c}\") / {t.scale_[i]}"

            elif t == "passthrough":
                yield f"ft.getDouble(\"{c}\")"

            elif t == "drop":
                continue

            else:
                raise Exception("Unknown transformer: " + t)
