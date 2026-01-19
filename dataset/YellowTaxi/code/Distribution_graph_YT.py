import matplotlib.pyplot as plt
import numpy as np

# === File paths ===
CLEAN_DIRTY_FILE = "dirty_ytd_2024-11_12.tbl"  # updated filename

'''
Clean mean: 28.19, std: 132.83, n=6614775
Dirty mean: 35.59, std: 138.62, n=6614775
X-axis range: (np.float64(-25031.177000000003), np.float64(352721.517))

'''

def read_amounts(path):
    clean_vals = []
    dirty_vals = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            fields = line.strip().split("|")
            if len(fields) < 5:
                continue
            try:
                clean_vals.append(float(fields[0]))  # clean total_amount
                dirty_vals.append(float(fields[2]))  # dirty total_amount
            except ValueError:
                continue
    return np.array(clean_vals), np.array(dirty_vals)

# --- Read data ---
clean_amounts, dirty_amounts = read_amounts(CLEAN_DIRTY_FILE)

# --- Basic statistics ---
clean_mean = np.mean(clean_amounts)
dirty_mean = np.mean(dirty_amounts)
clean_std = np.std(clean_amounts)
dirty_std = np.std(dirty_amounts)

# --- Axis limits ---
xmin = -10
xmax = 150
x_margin = (xmax - xmin) * 0.05
x_limits = (xmin - x_margin, xmax + x_margin)

# --- Plot ---
plt.figure(figsize=(12, 6))
bins = np.linspace(x_limits[0], x_limits[1], 100)

plt.hist(dirty_amounts, bins=bins, alpha=0.5, color="orange", label="Dirty Total Amount of km", density=False)
plt.hist(clean_amounts, bins=bins, alpha=0.5, color="steelblue", label="Clean Total Amount of km", density=False)

# Mean lines
plt.axvline(clean_mean, color="blue", linestyle="--", linewidth=1.5, label=f"Clean mean = {clean_mean:.2f}")
plt.axvline(dirty_mean, color="darkorange", linestyle="--", linewidth=1.5, label=f"Dirty mean = {dirty_mean:.2f}")

# Annotate means
ylim = plt.ylim()
plt.text(clean_mean, ylim[1]*0.9, f"{clean_mean:.2f}", color="blue", ha="left", va="bottom", fontsize=9)
plt.text(dirty_mean, ylim[1]*0.8, f"{dirty_mean:.2f}", color="darkorange", ha="left", va="bottom", fontsize=9)

plt.xlim(x_limits)
plt.xlabel("Total Amount")
plt.ylabel("Number of Rows")
plt.title("Total Amount Distribution: Clean vs Dirty Data (Yellow Taxi Dataset)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("graphs/total_amount_distribution_ytd.png", dpi=200)
plt.show()

# --- Print summary ---
print(f"Clean mean: {clean_mean:.2f}, std: {clean_std:.2f}, n={len(clean_amounts)}")
print(f"Dirty mean: {dirty_mean:.2f}, std: {dirty_std:.2f}, n={len(dirty_amounts)}")
print(f"X-axis range: {x_limits}")

