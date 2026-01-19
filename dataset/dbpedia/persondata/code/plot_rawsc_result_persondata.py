import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# === TRUE VALUES FOR PERSONDATA ===
TRUE_VALUES = {
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

OUTPUT_DIR = "graphs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_rawsc_result(agg_name):
    csv_file = f"rawsc_{agg_name}_results.csv"

    df = pd.read_csv(csv_file)

    # New CSV format already contains: sample_size, mu_xxx, ci_low, ci_high
    mean_col = [c for c in df.columns if c.startswith("mu_")][0]

    mu = df[mean_col]
    lo = df["ci_low"]
    hi = df["ci_high"]

    # Plot setup
    plt.figure(figsize=(10, 6))
    y_label = TRUE_VALUES[agg_name]["Y_LABEL"]

    # Horizontal true lines
    plt.axhline(TRUE_VALUES[agg_name]["ALL_DIRTY"],
                color="red", linestyle="--", linewidth=2, label="True Dirty")

    plt.axhline(TRUE_VALUES[agg_name]["ALL_CLEAN"],
                color="black", linestyle="--", linewidth=2, label="True Clean")

    # RawSC line + CI band
    plt.plot(df["sample_size"], mu,
             color="blue", marker="o", linewidth=2, label="RawSC Estimate")

    plt.fill_between(df["sample_size"], lo, hi,
                     color="blue", alpha=0.2, label="95% CI")

    # Labels
    plt.xlabel("Sample Size")
    plt.ylabel(y_label)
    plt.title(f"RawSC Estimation – {y_label}")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    # Save
    png_name = f"{OUTPUT_DIR}/rawsc_{agg_name}_plot.png"
    pdf_name = f"{OUTPUT_DIR}/rawsc_{agg_name}_plot.pdf"

    plt.savefig(png_name, dpi=300)
    plt.savefig(pdf_name)
    plt.close()

    print(f"✅ Saved {png_name} and {pdf_name}")


def main():
    for agg in ["count", "sum", "avg"]:
        try:
            plot_rawsc_result(agg)
        except FileNotFoundError:
            print(f"⚠️ Missing file rawsc_{agg}_results.csv — skipping.")


if __name__ == "__main__":
    main()

