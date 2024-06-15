#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import re

import sklearn
import sklearn.compose
import sklearn.ensemble
import sklearn.linear_model
import sklearn.svm

try:
    import lightning.regression
    import lightning.classification
except ValueError as e:
    print("Error during lightning import", e)

import xgboost as xgb
import lightgbm as lgb

from sympy.utilities.codegen import codegen


def powerset(iterable):
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s) + 1))


def create_regressor(trial, classifier_name, random_state):
    """ Create regressor model from given classifier """

    if classifier_name == 'mean':
        model = sklearn.dummy.DummyRegressor()

    elif classifier_name == 'SVR':
        kernel = trial.suggest_categorical('kernel', ['linear', 'poly', 'rbf', 'sigmoid'])
        svc_c = trial.suggest_float('svc_r', 1e-10, 1e10, log=True)
        model = sklearn.svm.SVR(C=svc_c, gamma='auto', kernel=kernel)

    elif classifier_name == 'QLatticeRegressor':
        from .models_feyn import QLatticeRegressor

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


def model_to_java(name, package, model_and_error: tuple, scaler, bounds, df):
    """ Convert to java source file """
    import m2cgen as m2c

    code = m2c.export_to_java(model_and_error[0], package, name)

    code, params = replace_params(code)

    imp = """import org.matsim.application.prepare.Predictor;
import it.unimi.dsi.fastutil.objects.Object2DoubleMap;
import it.unimi.dsi.fastutil.objects.Object2ObjectMap;
    
/**
* Generated model, do not modify.
* Model: %s
* Error: %f
*/
public final class""" % model_and_error

    code = code.replace("public class", imp)
    code = code.replace(name, name + " implements Predictor")

    features = [f"data[{i}] = {s};\n" for i, s in enumerate(model_features(scaler, df))]

    idx = code.index("public static double score")

    pre = """
    public static %s INSTANCE = new %s();
    public static final double[] DEFAULT_PARAMS = %s;

    @Override
    public double predict(Object2DoubleMap<String> features, Object2ObjectMap<String, String> categories) {
        return predict(features, categories, DEFAULT_PARAMS);
    }
    
    @Override
    public double[] getData(Object2DoubleMap<String> features, Object2ObjectMap<String, String> categories) {
        double[] data = new double[%d];
""" % (name, name, str(params).replace("[", "{").replace("]", "}"), len(features))

    for ft in features:
        pre += "\t\t" + ft

    ret = "score(data, params)" if bounds is None else "Math.min(Math.max(score(data, params), %f), %f)" % bounds

    pre += """
        return data;
    }
    
    @Override
    public double predict(Object2DoubleMap<String> features, Object2ObjectMap<String, String> categories, double[] params) {

        double[] data = getData(features, categories);
        for (int i = 0; i < data.length; i++)
            if (Double.isNaN(data[i])) throw new IllegalArgumentException("Invalid data at index: " + i);
    
        return %s;
    }
    """ % ret

    code = code.replace("score(double[] input)", "score(double[] input, double[] params)")

    return f"{code[:idx]}{pre}{code[idx:]}"


def model_to_py(name, model_and_error, scaler, df):
    import m2cgen as m2c

    code = m2c.export_to_python(model_and_error[0], function_name="score")

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
                    yield f"(features.getDouble(\"{c}\") - {t.mean_[i]}) / {t.scale_[i]}"
                else:
                    yield f"features.getDouble(\"{c}\") / {t.scale_[i]}"

            elif t == "passthrough":
                yield f"features.getDouble(\"{c}\")"

            elif t == "drop":
                continue

            else:
                raise Exception("Unknown transformer: " + t)
