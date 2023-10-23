# -*- coding: utf-8 -*-

import re

import pandas as pd
import seaborn as sns

from .utils import study_as_df


def plot_study(study):
    """ Create convergence plots for a study """

    modes = study.user_attrs["modes"]
    groups = study.user_attrs.get("groups", None)

    df = study_as_df(study)

    df_all = df[["trial"] + [x + "_mae" for x in modes]]

    df_all = pd.melt(df_all, "trial", var_name="main_mode", value_name="mae")
    df_all.main_mode = df_all.main_mode.str.removesuffix("_mae")

    ax = sns.lineplot(x="trial", y="mae", hue="main_mode", hue_order=modes, data=df_all)
    fig = ax.get_figure()

    fig.savefig("mae_all.png")

    if groups:

        for g in groups:

            p = re.compile(r"\[%s=(.+)\]-(.+)_mae" % g)

            columns = df.columns[df.columns.str.startswith("[" + g) & df.columns.str.endswith("_mae")]
            vars = [p.search(x) for x in columns]

            df_g = df[["trial"] + list(columns)]

            data = []

            # convert wide to long
            for idx, r in df_g.iterrows():
                for c, v in zip(columns, vars):
                    data.append({
                        "trial": r["trial"],
                        "mae": r[c],
                        g: v[1],
                        "main_mode": v[2]
                    })

            df_g = pd.DataFrame(data)

            grid = sns.FacetGrid(df_g, col=g)
            grid.map_dataframe(sns.lineplot, x="trial", y="mae", hue="main_mode", hue_order=modes)

            grid.figure.savefig("mae_%s.png" % g)
