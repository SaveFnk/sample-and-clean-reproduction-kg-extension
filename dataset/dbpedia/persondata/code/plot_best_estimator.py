import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# CONFIG
# ----------------------------
ALL_RESULTS = {
    "count": {
        "ALL_CLEAN": 613207,
        "ALL_DIRTY": 736110,
        "Y_LABEL": "COUNT"
    },
    "sum": {
        "ALL_CLEAN": 1182229731,
        "ALL_DIRTY": 1670534580,
        "Y_LABEL": "SUM"
    },
    "avg": {
        "ALL_CLEAN": 1927.9455893360644,
        "ALL_DIRTY": 2269.4088926926684,
        "Y_LABEL": "AVG (Birth Year)"
    }
}


# ----------------------------
# MAIN FUNCTION
# ----------------------------
def plot_best_estimator(agg_name):

    # new expected filenames
    raw_file = f"rawsc_{agg_name}_results.csv"
    norm_file = f"normsc_{agg_name}_results.csv"

    raw = pd.read_csv(raw_file)
    norm = pd.read_csv(norm_file)

    # -------------------------
    # Process RAWSC file
    # -------------------------
    raw = raw.rename(columns={
        f"mu_{agg_name}": "mean",
        "ci_low": "ci_low",
        "ci_high": "ci_high"
    })

    raw["ci_width"] = raw["ci_high"] - raw["ci_low"]
    raw["estimator"] = "RawSC"

    # -------------------------
    # Process NormSC file
    # -------------------------
    norm = norm.rename(columns={
        f"normsc_{agg_name}": "mean",
        f"ci_{agg_name}": "ci_halfwidth"
    })

    # NormSC CI is mean ± ci_halfwidth
    norm["ci_low"] = norm["mean"] - norm["ci_halfwidth"]
    norm["ci_high"] = norm["mean"] + norm["ci_halfwidth"]
    norm["ci_width"] = 2 * norm["ci_halfwidth"]
    norm["estimator"] = "NormSC"

    # -------------------------
    # Merge both
    # -------------------------
    merged = pd.concat([raw, norm], ignore_index=True)
    merged_sorted = merged.sort_values("sample_size")

    # Pick estimator with smallest CI width
    best_idx = merged_sorted.groupby("sample_size")["ci_width"].idxmin()
    best = merged_sorted.loc[best_idx]
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

    # best estimator line + CI
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

    # non-best estimator as X's
    plt.scatter(
        nonbest["sample_size"],
        nonbest["mean"],
        marker="x",
        color="blue",
        label="Other Estimator"
    )

    plt.xlabel("Sample Size")
    plt.ylabel(f"Query Result ({y_label})")
    plt.title(f"Best Estimator (RawSC or NormSC) for {y_label.upper()}")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    plt.savefig(f"graphs/best_{agg_name}_plot.png", dpi=300)
    plt.savefig(f"graphs/best_{agg_name}_plot.pdf")
    plt.close()

    print(f"✅ Saved best_{agg_name}_plot_dbp.png/.pdf")


def main():
    for agg in ["avg", "count", "sum"]:
        plot_best_estimator(agg)


if __name__ == "__main__":
    main()

