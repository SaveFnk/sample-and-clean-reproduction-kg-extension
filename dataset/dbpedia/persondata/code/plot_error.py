import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# === CONFIGURATION ===
ALL_RESULTS = {
    "count": {
        "ALL_CLEAN": 613207,
        "ALL_DIRTY": 736110,
        "LABEL": "COUNT"
    },
    "sum": {
        "ALL_CLEAN": 1182229731,
        "ALL_DIRTY": 1670534580,
        "LABEL": "SUM"
    },
    "avg": {
        "ALL_CLEAN": 1927.9455893360644,
        "ALL_DIRTY": 2269.4088926926684,
        "LABEL": "AVG (Birth Year)"
    }
}


def plot_ci_percentage_error(agg_name):

    # Load CSVs
    raw = pd.read_csv(f"rawsc_{agg_name}_results.csv")
    norm = pd.read_csv(f"normsc_{agg_name}_results.csv")

    raw = raw.sort_values("sample_size")
    norm = norm.sort_values("sample_size")

    clean = ALL_RESULTS[agg_name]["ALL_CLEAN"]
    dirty = ALL_RESULTS[agg_name]["ALL_DIRTY"]

    # --------------------------
    #   RAWSC CI HANDLING
    # --------------------------
    # raw file always contains:
    #   mu_<agg>, ci_low, ci_high
    mean_col_raw = f"mu_{agg_name}"
    raw["ci_width"] = raw["ci_high"] - raw["ci_low"]
    # convert CI half-width in % error
    raw["ci_pct"] = (raw["ci_width"] / 2) / clean * 100

    # --------------------------
    #   NORMALIZEDSC CI HANDLING
    # --------------------------
    # norm contains:
    #   normsc_<agg>, ci_<agg>  (ci_avg, ci_sum, ci_count)
    mean_col_norm = f"normsc_{agg_name}"
    ci_col_norm = f"ci_{agg_name}"

    norm["ci_pct"] = norm[ci_col_norm] / clean * 100

    # --------------------------
    #   PLOT
    # --------------------------
    plt.figure(figsize=(8, 6))

    # Dirty reference line
    norm_ci_dirty = abs(dirty - clean) / clean * 100
    plt.axhline(norm_ci_dirty, color="red", linestyle="--",
                label="AllDirty baseline")

    # RawSC
    plt.plot(
        raw["sample_size"], raw["ci_pct"],
        marker="^", color="blue", label="RawSC CI%"
    )

    # NormalizedSC
    plt.plot(
        norm["sample_size"], norm["ci_pct"],
        marker="o", color="black", label="NormalizedSC CI%"
    )

    plt.xlabel("Sample Size")
    plt.ylabel("CI Half-Width (%)")
    plt.title(f"Confidence Interval % Error — {ALL_RESULTS[agg_name]['LABEL']}")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()

    plt.savefig(f"graphs/ci_error_{agg_name}_dbp.png", dpi=300)
    plt.savefig(f"graphs/ci_error_{agg_name}_dbp.pdf")
    plt.close()

    print(f"✅ Saved graphs/ci_error_{agg_name}_dbp.[png/pdf]")


def main():
    for agg in ["avg", "count", "sum"]:
        plot_ci_percentage_error(agg)


if __name__ == "__main__":
    main()

