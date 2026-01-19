import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

Z = 1.96  # 95% confidence

# === CONFIGURATION ===
ALL_RESULTS = {
    "count": {"ALL_DIRTY": 5650714, "ALL_CLEAN": 5059647, "LABEL": "COUNT"},
    "sum":   {"ALL_DIRTY": 196872450, "ALL_CLEAN": 138787132, "LABEL": "SUM"},
    "avg":   {"ALL_DIRTY": 34.84, "ALL_CLEAN": 27.43, "LABEL": "AVG"},
}


def plot_ci_percentage_error(agg_name):

    # Load RawSC + NormSC (Yellow Taxi)
    raw = pd.read_csv(f"rawsc_{agg_name}_results_ytd.csv")
    norm = pd.read_csv(f"normalizedsc_{agg_name}_results_ytd.csv")

    # Sort
    raw = raw.sort_values("sample_size")
    norm = norm.sort_values("sample_size")

    # True clean value
    clean_val = ALL_RESULTS[agg_name]["ALL_CLEAN"]
    dirty_val = ALL_RESULTS[agg_name]["ALL_DIRTY"]

    # Compute CIs for both estimators
    for df in [raw, norm]:
        df["stderr"] = np.sqrt(df["variance"] / df["sample_size"])
        df["ci_low"] = df["mean"] - Z * df["stderr"]
        df["ci_high"] = df["mean"] + Z * df["stderr"]
        df["ci_width"] = df["ci_high"] - df["ci_low"]
        df["ci_pct"] = df["ci_width"] / clean_val * 100

    # Dirty baseline error (precomputed in paper)
    dirty_error = abs(dirty_val - clean_val) / clean_val * 100

    # --------------------
    # PLOT
    # --------------------
    plt.figure(figsize=(8, 6))

    # Red horizontal AllDirty reference
    plt.axhline(y=dirty_error,
                color="red",
                linestyle="--",
                linewidth=2,
                label="AllDirty")

    # CI width % for RawSC
    plt.plot(raw["sample_size"], raw["ci_pct"],
             marker="^", color="blue", label="RawSC (CI width %)")

    # CI width % for NormalizedSC
    plt.plot(norm["sample_size"], norm["ci_pct"],
             marker="o", color="black", label="NormalizedSC (CI width %)")

    plt.xlabel("Number of Cleaned Samples")
    plt.ylabel("CI Width (% of Clean Value)")
    plt.title(f"Confidence-Interval Error for {ALL_RESULTS[agg_name]['LABEL']} (Yellow Taxi)")

    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()

    plt.savefig(f"graphs/ci_error_{agg_name}_ytd.png", dpi=300)
    plt.savefig(f"graphs/ci_error_{agg_name}_ytd.pdf")
    plt.close()

    print(f"✅ Saved graphs/ci_error_{agg_name}_ytd.png and PDF")


def main():
    for agg in ["avg", "count", "sum"]:
        plot_ci_percentage_error(agg)


if __name__ == "__main__":
    main()

