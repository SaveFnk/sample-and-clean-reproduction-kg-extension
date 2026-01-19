import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === CONFIGURATION ===
ALL_RESULTS = {
    "count": {"ALL_DIRTY": 1656658, "ALL_CLEAN": 1478493, "Y_LABEL": "COUNT"},
    "sum":   {"ALL_DIRTY": 52950112, "ALL_CLEAN": 37734107, "Y_LABEL": "SUM"},
    "avg":   {"ALL_DIRTY": 31.97, "ALL_CLEAN": 25.52, "Y_LABEL": "AVG"},
}

NUMBER_ELEM = 6000000


def plot_rawsc_result(agg_name):
    # ============================================
    # Load original RawSC results (blue)
    # ============================================
    csv_file = f"rawsc_{agg_name}_results.csv"
    df = pd.read_csv(csv_file)

    df["stderr"] = np.sqrt(df["variance"] / df["sample_size"])
    df["ci_low"] = df["mean"] - 1.96 * df["stderr"]
    df["ci_high"] = df["mean"] + 1.96 * df["stderr"]

    # ============================================
    # NEW: Load averaged RawSC results (green)
    # ============================================
    avg_csv = f"rawsc_averaged_{agg_name}_results.csv"
    try:
        df_avg = pd.read_csv(avg_csv)
        has_avg = True
    except FileNotFoundError:
        print(f"⚠️ Averaged results not found: {avg_csv} — skipping green line.")
        has_avg = False

    # ============================================
    # Plot setup
    # ============================================
    plt.figure(figsize=(10, 6))
    y_label = ALL_RESULTS[agg_name]["Y_LABEL"]

    # Horizontal baseline lines
    plt.axhline(ALL_RESULTS[agg_name]["ALL_DIRTY"],
                color="red", linestyle=":", linewidth=2, label="All Dirty")

    plt.axhline(ALL_RESULTS[agg_name]["ALL_CLEAN"],
                color="black", linestyle=":", linewidth=2, label="All Clean")

    # ============================================
    # Original RawSC (blue) + CI
    # ============================================
    plt.plot(df["sample_size"], df["mean"],
             color="blue", marker="o", label="RawSC Estimate")
    plt.fill_between(df["sample_size"], df["ci_low"], df["ci_high"],
                     color="blue", alpha=0.2)

    # ============================================
    # NEW: Averaged RawSC (green), no CI
    # ============================================
    if has_avg:
        plt.plot(df_avg["sample_size"], df_avg["mean"],
                 color="green", marker="s", linewidth=2,
                 label="Averaged RawSC (5 subsets)")

    # ============================================
    # Labels and export
    # ============================================
    plt.xlabel("Sample Size")
    plt.ylabel(f"Query Result ({y_label})")
    plt.title(f"RawSC Estimation for {y_label.upper()} (TPC-H Lineitem)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    png_name = f"graphs/rawsc_averaged_{agg_name}_plot.png"
    pdf_name = f"graphs/rawsc_averaged_{agg_name}_plot.pdf"
    plt.savefig(png_name, dpi=300)
    plt.savefig(pdf_name)
    plt.close()

    print(f"✅ Saved {png_name} and {pdf_name}")


def main():
    for agg in ["count", "sum", "avg"]:
        try:
            plot_rawsc_result(agg)
        except FileNotFoundError:
            print(f"⚠️ Missing file: rawsc_averaged_{agg}_results.csv — skipping.")


if __name__ == "__main__":
    main()

