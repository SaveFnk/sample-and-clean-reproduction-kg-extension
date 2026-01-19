import os
import glob
import csv
import numpy as np

# === Configuration ===
INPUT_DIR = "sample/"
PRED_RETURNFLAG = "A"
PRED_LINESTATUS = "F"

# Total population size (including duplicates)
N = 7201871  

# All Dirty aggregate results (from full dirty_lineitem.tbl)
ALL_DIRTY = {
    "count": 1657329,     # COUNT(*)
    "sum":   52998967.0,  # SUM(quantity)
    "avg":   31.97         # AVG(quantity)
}

# === Helper ===
def parse_line(line):
    parts = line.strip().split("|")
    if len(parts) < 7:
        return None
    try:
        clean_qty = float(parts[0])
        clean_return = parts[1].strip()
        clean_status = parts[2].strip()
        dirty_qty = float(parts[3])
        dirty_return = parts[4].strip()
        dirty_status = parts[5].strip()
        numdup = float(parts[6])
        return (
            clean_qty, clean_return, clean_status,
            dirty_qty, dirty_return, dirty_status,
            numdup
        )
    except ValueError:
        return None


def process_sample_file(filepath):
    """Compute NormalizedSC correction for COUNT, SUM, AVG."""
    clean_vals, dirty_vals = [], []
    preds_clean, preds_dirty, numdups = [], [], []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            parsed = parse_line(line)
            if parsed is None:
                continue
            (
                cq, cr, cs,
                dq, dr, ds,
                numdup
            ) = parsed

            # Predicate: returnflag='A' AND linestatus='F'
            pred_clean = int(cr == PRED_RETURNFLAG and cs == PRED_LINESTATUS)
            pred_dirty = int(dr == PRED_RETURNFLAG and ds == PRED_LINESTATUS)

            clean_vals.append(cq)
            dirty_vals.append(dq)
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

    # Duplication rate (for clean side)
    d = K / np.sum(1.0 / numdups)

    # === φ_dirty(t) and φ_clean(t) ===
    # COUNT
    phi_count_dirty = preds_dirty * N
    phi_count_clean = preds_clean * (N / numdups)

    # SUM
    phi_sum_dirty = preds_dirty * (N * dirty_vals)
    phi_sum_clean = preds_clean * (N * clean_vals / numdups)

    # AVG
    phi_avg_dirty = preds_dirty * (K / K_pred_dirty) * dirty_vals
    phi_avg_clean = preds_clean * (d * K / K_pred_clean) * (clean_vals / numdups)

    # === q(t) = φ_dirty - φ_clean ===
    q_count = phi_count_dirty - phi_count_clean
    q_sum = phi_sum_dirty - phi_sum_clean
    q_avg = phi_avg_dirty - phi_avg_clean

    # === Mean and variance of q ===
    mean_q_count, var_q_count = np.mean(q_count), np.var(q_count, ddof=1)
    mean_q_sum, var_q_sum = np.mean(q_sum), np.var(q_sum, ddof=1)
    mean_q_avg, var_q_avg = np.mean(q_avg), np.var(q_avg, ddof=1)

    # === NormalizedSC estimates ===
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
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "sample_lineitem_*.tbl")))
    if not files:
        print("No sample files found in", INPUT_DIR)
        return

    for file in files:
        sample_size = int(os.path.basename(file).split("_")[-1].split(".")[0])
        res = process_sample_file(file)
        if res is None:
            print(f"Skipping {file} (empty or invalid).")
            continue
        for agg in ["count", "sum", "avg"]:
            mean, var = res[agg]
            results[agg].append((sample_size, mean, var))
        print(f"Processed {file} ✅")

    # Write results
    for agg, data in results.items():
        csv_path = f"normalizedsc_{agg}_results.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["sample_size", "mean", "variance"])
            writer.writerows(sorted(data))
        print(f"Saved results → {csv_path}")

    print("All done!")


if __name__ == "__main__":
    main()

