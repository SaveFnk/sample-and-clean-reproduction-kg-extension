import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === CONFIGURATION ===
# Replace these with the actual results from your ALL CLEAN / ALL DIRTY run
ALL_RESULTS = {
    "count": {"ALL_DIRTY": 1656658, "ALL_CLEAN": 1478493, "Y_LABEL": "COUNT"},
    "sum":   {"ALL_DIRTY": 52950112, "ALL_CLEAN": 37734107, "Y_LABEL": "SUM"},
    "avg":   {"ALL_DIRTY": 31.97, "ALL_CLEAN": 25.52, "Y_LABEL": "AVG"},
}

# Default total number of elements (only used for axis scaling if needed)
NUMBER_ELEM = 6000000

# === FUNCTION ===
def plot_rawsc_result(agg_name):
    csv_file = f"rawsc_{agg_name}_results.csv"
    df = pd.read_csv(csv_file)

    # Compute confidence intervals
    df["stderr"] = np.sqrt(df["variance"] / df["sample_size"])
    df["ci_low"] = df["mean"] - 1.96 * df["stderr"]
    df["ci_high"] = df["mean"] + 1.96 * df["stderr"]

    # Plot setup
    plt.figure(figsize=(10, 6))
    y_label = ALL_RESULTS[agg_name]["Y_LABEL"]

    # Horizontal baselines
    plt.axhline(
        ALL_RESULTS[agg_name]["ALL_DIRTY"],
        color="red", linestyle=":", linewidth=2, label="All Dirty"
    )
    plt.axhline(
        ALL_RESULTS[agg_name]["ALL_CLEAN"],
        color="black", linestyle=":", linewidth=2, label="All Clean"
    )

    # RawSC line + CI
    plt.plot(df["sample_size"], df["mean"], color="blue", marker="o", label="RawSC Estimate")
    plt.fill_between(df["sample_size"], df["ci_low"], df["ci_high"], color="blue", alpha=0.2)

    plt.xlabel("Sample Size")
    plt.ylabel(f"Query Result ({y_label})")
    plt.title(f"RawSC Estimation for {y_label.upper()} (TPC-H Lineitem)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    # Save to files
    png_name = f"graphs/rawsc_{agg_name}_plot.png"
    pdf_name = f"graphs/rawsc_{agg_name}_plot.pdf"
    plt.savefig(png_name, dpi=300)
    plt.savefig(pdf_name)
    plt.close()

    print(f"✅ Saved {png_name} and {pdf_name}")


def main():
    for agg in ["count", "sum", "avg"]:
        try:
            plot_rawsc_result(agg)
        except FileNotFoundError:
            print(f"⚠️ Missing file: rawsc_{agg}_results.csv — skipping.")


if __name__ == "__main__":
    main()

