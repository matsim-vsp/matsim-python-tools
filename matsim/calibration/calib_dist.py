# -*- coding: utf-8 -*-

# TODO: collection of old code
# was just draft anyway, needs to be updated

"""
m["marginalUtilityOfDistance_util_m"] = trial.suggest_float("dist_" + mode, sys.float_info.min,
                                                                            sys.float_info.max)


def sample_dist_util(self, mode, last):

        df = pd.DataFrame.from_dict(last.user_attrs["mode_stats"], orient="tight")
        target = self.target[self.target["mode"] == mode].reset_index(drop=True).copy()

        df = df.loc[target.dist_group].reset_index()

        # Trips distances shares over all modes
        # Correction factor is calculated here
        ref_dist = self.target.groupby("dist_group").agg(share=("share", "sum"))
        sim_dist = df.groupby("dist_group").agg(share=("share", "sum"))

        correction = ref_dist.loc[target.dist_group] / sim_dist.loc[target.dist_group]

        df = df[df.main_mode == mode].reset_index(drop=True).copy()

        if "mean_dist" not in target.columns:
            target["mean_dist"] = df.mean_dist

        df["correction"] = correction.values

        target.share = target.share / sum(target.share)
        df.share = df.share / sum(df.share)

        real = (df.mean_dist * df.share * df.correction).sum()
        target = (target.mean_dist * target.share).sum()

        # TODO: magnitude should depend on the asc

        # TODO: configurable parameter
        return float(0.05 * (target - real) / (1000 * 1000))

"""