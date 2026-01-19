import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

Z = 1.96  # 95% CI

# === CONFIGURATION ===
ALL_RESULTS = {
    "avg":  {"ALL_DIRTY": 31.97,    "ALL_CLEAN": 25.52,    "LABEL": "AVG"},
    "sum":  {"ALL_DIRTY": 52950112, "ALL_CLEAN": 37734107, "LABEL": "SUM"},
    "count":{"ALL_DIRTY": 1656658,  "ALL_CLEAN": 1478493,  "LABEL": "COUNT"},
}

def plot_ci_percentage_error(agg_name):

    # Load RawSC + NormSC
    raw = pd.read_csv(f"rawsc_{agg_name}_results.csv")
    norm = pd.read_csv(f"normalizedsc_{agg_name}_results.csv")

    # Sort by sample size
    raw = raw.sort_values("sample_size")
    norm = norm.sort_values("sample_size")

    # Clean value for normalization
    clean_val = ALL_RESULTS[agg_name]["ALL_CLEAN"]

    # --- Compute confidence intervals ---
    for df in [raw, norm]:
        df["stderr"] = np.sqrt(df["variance"] / df["sample_size"])
        df["ci_low"] = df["mean"] - Z * df["stderr"]
        df["ci_high"] = df["mean"] + Z * df["stderr"]
        df["ci_width"] = df["ci_high"] - df["ci_low"]

    # CI width as percentage of clean value
    raw["ci_pct"]  = raw["ci_width"]  / clean_val * 100
    norm["ci_pct"] = norm["ci_width"] / clean_val * 100

    # Dirty baseline error (same used in paper)
    dirty_val = ALL_RESULTS[agg_name]["ALL_DIRTY"]
    dirty_error = abs(dirty_val - clean_val) / clean_val * 100

    # --- Plot ---
    plt.figure(figsize=(8, 6))

    # Dirty reference line
    plt.axhline(y=dirty_error,
                color="red",
                linestyle="--",
                linewidth=2,
                label="AllDirty")

    # RawSC curve
    plt.plot(raw["sample_size"], raw["ci_pct"],
             marker="^", color="blue", label="RawSC (CI width %)")

    # NormalizedSC curve
    plt.plot(norm["sample_size"], norm["ci_pct"],
             marker="o", color="black", label="NormalizedSC (CI width %)")

    plt.xlabel("Number of Cleaned Samples")
    plt.ylabel("CI Width (% of Clean Value)")
    plt.title(f"Confidence-Interval Error for {ALL_RESULTS[agg_name]['LABEL']}")

    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()

    plt.savefig(f"graphs/ci_error_{agg_name}.png", dpi=300)
    plt.savefig(f"graphs/ci_error_{agg_name}.pdf")
    plt.close()

    print(f"✅ Saved graphs/ci_error_{agg_name}.png and PDF")

def main():
    for agg in ["avg", "count", "sum"]:
        plot_ci_percentage_error(agg)

if __name__ == "__main__":
    main()

