import matplotlib.pyplot as plt
import numpy as np

# === File paths ===
CLEAN_DIRTY_FILE = "dirty_lineitem.tbl"

def read_quantities(path):
    clean_q = []
    dirty_q = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            fields = line.strip().split("|")
            if len(fields) < 7:
                continue
            try:
                clean_q.append(float(fields[0]))
                dirty_q.append(float(fields[3]))
            except ValueError:
                continue
    return np.array(clean_q), np.array(dirty_q)

# --- Read data ---
clean_quantities, dirty_quantities = read_quantities(CLEAN_DIRTY_FILE)

# --- Basic statistics ---
clean_mean = np.mean(clean_quantities)
dirty_mean = np.mean(dirty_quantities)
clean_std = np.std(clean_quantities)
dirty_std = np.std(dirty_quantities)

# --- Axis limits ---
xmin = min(np.min(clean_quantities), np.min(dirty_quantities))
xmax = max(np.max(clean_quantities), np.max(dirty_quantities))
x_margin = (xmax - xmin) * 0.05
x_limits = (xmin - x_margin, xmax + x_margin)

# --- Plot ---
plt.figure(figsize=(12, 6))
bins = np.linspace(x_limits[0], x_limits[1], 100)

plt.hist(dirty_quantities, bins=bins, alpha=0.5, color="orange", label="Dirty Quantities", density=False)
plt.hist(clean_quantities, bins=bins, alpha=0.5, color="steelblue", label="Clean Quantities", density=False)

# Mean lines
plt.axvline(clean_mean, color="blue", linestyle="--", linewidth=1.5, label=f"Clean mean = {clean_mean:.2f}")
plt.axvline(dirty_mean, color="darkorange", linestyle="--", linewidth=1.5, label=f"Dirty mean = {dirty_mean:.2f}")

# Annotate means
ylim = plt.ylim()
plt.text(clean_mean, ylim[1]*0.9, f"{clean_mean:.1f}", color="blue", ha="left", va="bottom", fontsize=9)
plt.text(dirty_mean, ylim[1]*0.8, f"{dirty_mean:.1f}", color="darkorange", ha="left", va="bottom", fontsize=9)

plt.xlim(x_limits)
plt.xlabel("Quantity")
plt.ylabel("Number of rows")
plt.title("Quantity Distribution: Clean vs Dirty Data (TPC-H)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("quantity_distribution_tpc_h.png", dpi=200)
plt.show()

# --- Print summary ---
print(f"Clean mean: {clean_mean:.2f}, std: {clean_std:.2f}, n={len(clean_quantities)}")
print(f"Dirty mean: {dirty_mean:.2f}, std: {dirty_std:.2f}, n={len(dirty_quantities)}")
print(f"X-axis range: {x_limits}")

