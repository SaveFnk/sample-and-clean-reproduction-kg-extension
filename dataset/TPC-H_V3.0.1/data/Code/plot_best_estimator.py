import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# CONFIG
# ----------------------------
ALL_RESULTS = {
    "avg":  {"ALL_DIRTY": 31.97,   "ALL_CLEAN": 25.52,    "Y_LABEL": "AVG"},
    "sum":  {"ALL_DIRTY": 52950112, "ALL_CLEAN": 37734107, "Y_LABEL": "SUM"},
    "count":{"ALL_DIRTY": 1656658, "ALL_CLEAN": 1478493,  "Y_LABEL": "COUNT"},
}

Z = 1.96   # 95% CI


# ----------------------------
# MAIN FUNCTION
# ----------------------------
def plot_best_estimator(agg_name):

    raw_file = f"rawsc_{agg_name}_results.csv"
    norm_file = f"normalizedsc_{agg_name}_results.csv"

    raw = pd.read_csv(raw_file)
    norm = pd.read_csv(norm_file)

    # compute CI
    raw["stderr"] = np.sqrt(raw["variance"] / raw["sample_size"])
    raw["ci_low"] = raw["mean"] - Z * raw["stderr"]
    raw["ci_high"] = raw["mean"] + Z * raw["stderr"]
    raw["ci_width"] = raw["ci_high"] - raw["ci_low"]
    raw["estimator"] = "RawSC"

    norm["stderr"] = np.sqrt(norm["variance"] / norm["sample_size"])
    norm["ci_low"] = norm["mean"] - Z * norm["stderr"]
    norm["ci_high"] = norm["mean"] + Z * norm["stderr"]
    norm["ci_width"] = norm["ci_high"] - norm["ci_low"]
    norm["estimator"] = "NormSC"

    # merge
    merged = pd.concat([raw, norm], ignore_index=True)

    # select best estimator per sample_size
    merged_sorted = merged.sort_values("sample_size")
    best_idx = merged_sorted.groupby("sample_size")["ci_width"].idxmin()
    best = merged_sorted.loc[best_idx]

    # identify non-selected points
    nonbest = merged_sorted.drop(best_idx)

    # ----------------------------
    # PLOT
    # ----------------------------
    plt.figure(figsize=(12, 7))
    y_label = ALL_RESULTS[agg_name]["Y_LABEL"]

    # baselines
    plt.axhline(ALL_RESULTS[agg_name]["ALL_DIRTY"],
                color="red", linestyle=":", linewidth=2, label="All Dirty")

    plt.axhline(ALL_RESULTS[agg_name]["ALL_CLEAN"],
                color="black", linestyle=":", linewidth=2, label="All Clean")

    # best estimator — blue, continuous line + error bars
    plt.errorbar(
        best["sample_size"],
        best["mean"],
        yerr=[best["mean"] - best["ci_low"], best["ci_high"] - best["mean"]],
        fmt="o-",
        color="blue",
        ecolor="blue",
        elinewidth=1.3,
        capsize=4,
        label="Best Estimator (SC)"
    )

    # non-best estimator — blue X (NO line, NO CI)
    plt.scatter(
        nonbest["sample_size"],
        nonbest["mean"],
        marker="x",
        color="blue",
        label="Other Estimator"
    )

    plt.xlabel("Sample Size")
    plt.ylabel(f"Query Result ({y_label})")
    plt.title(f"Best Estimator (RawSC or NormalizedSC) for {y_label.upper()}")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    plt.savefig(f"graphs/best_{agg_name}_plot.png", dpi=300)
    plt.savefig(f"graphs/best_{agg_name}_plot.pdf")
    plt.close()

    print(f"✅ Saved best_{agg_name}_plot.png/.pdf")


def main():
    for agg in ["avg", "count", "sum"]:
        plot_best_estimator(agg)


if __name__ == "__main__":
    main()

