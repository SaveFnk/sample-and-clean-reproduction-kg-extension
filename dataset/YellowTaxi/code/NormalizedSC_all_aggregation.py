import os
import glob
import csv
import numpy as np
#####                    YELLOW TAXI

# === Configuration ===
INPUT_DIR = "sample/"
PRED_PASSENGER = 1   # passenger_count == 1

# Total population size AFTER applying duplication process
N = 7937540  # adjust if needed

# Fill these values using compute_aggregates on dirty_ytd_2024-11_12.tbl
ALL_DIRTY = {
    "count": 5650714,      # COUNT(*)
    "sum":   196872450,    # SUM(total_amount)
    "avg":   34.84         # AVG(total_amount)
}

# === Helper ===
def parse_line(line):
    parts = line.strip().split("|")
    if len(parts) < 5:
        return None
    try:
        clean_total = float(parts[0])
        clean_pass  = float(parts[1])
        dirty_total = float(parts[2])
        dirty_pass  = float(parts[3])
        numdup      = float(parts[4])
        return clean_total, clean_pass, dirty_total, dirty_pass, numdup
    except ValueError:
        return None


def process_sample_file(filepath):
    """Compute NormalizedSC correction for COUNT, SUM, AVG."""
    clean_vals, dirty_vals = [], []
    preds_clean, preds_dirty, numdups = [], [], []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            parsed = parse_line(line)
            if parsed is None:
                continue
            clean_total, clean_pass, dirty_total, dirty_pass, numdup = parsed

            # Predicate: passenger_count == 1
            pred_clean = float(clean_pass == PRED_PASSENGER)
            pred_dirty = float(dirty_pass == PRED_PASSENGER)

            clean_vals.append(clean_total)
            dirty_vals.append(dirty_total)
            preds_clean.append(pred_clean)
            preds_dirty.append(pred_dirty)
            numdups.append(numdup)

    K = len(clean_vals)
    if K == 0:
        return None

    clean_vals = np.array(clean_vals)
    dirty_vals = np.array(dirty_vals)
    preds_clean = np.array(preds_clean)
    preds_dirty = np.array(preds_dirty)
    numdups = np.array(numdups)

    K_pred_clean = np.sum(preds_clean)
    K_pred_dirty = np.sum(preds_dirty)
    if K_pred_clean == 0 and K_pred_dirty == 0:
        return None

    # Duplication rate
    d = K / np.sum(1.0 / numdups)

    # === φ_dirty and φ_clean ===
    # COUNT
    phi_count_dirty = preds_dirty * N
    phi_count_clean = preds_clean * (N / numdups)

    # SUM
    phi_sum_dirty = preds_dirty * (N * dirty_vals)
    phi_sum_clean = preds_clean * (N * clean_vals / numdups)

    # AVG
    phi_avg_dirty = preds_dirty * (K / K_pred_dirty) * dirty_vals
    phi_avg_clean = preds_clean * (d * K / K_pred_clean) * (clean_vals / numdups)

    # q(t) = φ_dirty(t) − φ_clean(t)
    q_count = phi_count_dirty - phi_count_clean
    q_sum = phi_sum_dirty - phi_sum_clean
    q_avg = phi_avg_dirty - phi_avg_clean

    # Mean and variance
    mean_q_count, var_q_count = np.mean(q_count), np.var(q_count, ddof=1)
    mean_q_sum, var_q_sum = np.mean(q_sum), np.var(q_sum, ddof=1)
    mean_q_avg, var_q_avg = np.mean(q_avg), np.var(q_avg, ddof=1)

    # NormalizedSC final estimates
    est_count = ALL_DIRTY["count"] - mean_q_count
    est_sum   = ALL_DIRTY["sum"]   - mean_q_sum
    est_avg   = ALL_DIRTY["avg"]   - mean_q_avg

    return {
        "K": K,
        "count": (est_count, var_q_count),
        "sum": (est_sum, var_q_sum),
        "avg": (est_avg, var_q_avg),
    }


def main():
    results = {"count": [], "sum": [], "avg": []}

    # NEW SAMPLE FILENAME PATTERN
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "sample_ytd_*.tbl")))
    if not files:
        print("No sample files found in sample/")
        return

    for file in files:
        sample_size = int(os.path.basename(file).split("_")[-1].split(".")[0])
        res = process_sample_file(file)
        if res is None:
            print(f"Skipping {file} (no predicate matches).")
            continue

        for agg in ["count", "sum", "avg"]:
            mean, var = res[agg]
            results[agg].append((sample_size, mean, var))

        print(f"Processed {file} ✅")

    # Write results
    for agg, data in results.items():
        csv_path = f"normalizedsc_{agg}_results_ytd.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["sample_size", "mean", "variance"])
            writer.writerows(sorted(data))
        print(f"Saved → {csv_path}")

    print("Done.")


if __name__ == "__main__":
    main()

