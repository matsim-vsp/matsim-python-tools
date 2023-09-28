# -*- coding: utf-8 -*-
"""These models depend on the feyn package which is not listed and only optional due to its licensing"""

from time import time

import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, RegressorMixin, ClassifierMixin
from sklearn.metrics import mean_squared_error

import feyn

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