import os
import glob
import csv
import numpy as np

# === Configuration ===
INPUT_DIR = "sample/"
PRED_RETURNFLAG = "A"
PRED_LINESTATUS = "F"

N = 7201871  # total population size 

# === Helper ===
def parse_line(line):
    parts = line.strip().split("|")
    if len(parts) < 7:
        return None
    try:
        clean_qty = float(parts[0])
        returnflag = parts[1].strip()
        linestatus = parts[2].strip()
        numdup = float(parts[6])
        return clean_qty, returnflag, linestatus, numdup
    except ValueError:
        return None


def process_sample_file(filepath):
    """Read a sample_lineitem_*.tbl and compute RawSC stats for AVG, SUM, COUNT."""
    clean_vals = []
    preds = []
    numdups = []

    # --- Read and filter by predicate ---
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            parsed = parse_line(line)
            if parsed is None:
                continue
            qty, returnflag, linestatus, numdup = parsed

            # Predicate: returnflag='A' AND linestatus='F'
            pred = int(returnflag == PRED_RETURNFLAG and linestatus == PRED_LINESTATUS)
            clean_vals.append(qty)
            preds.append(pred)
            numdups.append(numdup)

    K = len(clean_vals)
    if K == 0:
        return None

    clean_vals = np.array(clean_vals)
    preds = np.array(preds)
    numdups = np.array(numdups)

    # --- Precompute counts ---
    K_pred = np.sum(preds)
    if K_pred == 0:
        return None

    # Duplication rate
    d = K / np.sum(1.0 / numdups)

    # --- Compute φ_clean(t) for each aggregate ---
    phi_count = preds * (N / numdups)
    phi_sum   = preds * (N * clean_vals / numdups)
    phi_avg   = preds * (d * K / K_pred) * (clean_vals / numdups)

    # --- Compute mean and variance for each ---
    mean_count, var_count = np.mean(phi_count), np.var(phi_count, ddof=1)
    mean_sum, var_sum = np.mean(phi_sum), np.var(phi_sum, ddof=1)
    mean_avg, var_avg = np.mean(phi_avg), np.var(phi_avg, ddof=1)

    return {
        "K": K,
        "count": (mean_count, var_count),
        "sum": (mean_sum, var_sum),
        "avg": (mean_avg, var_avg),
    }


def main():
    results = {"count": [], "sum": [], "avg": []}

    # Collect all sample files
    files = sorted(glob.glob(os.path.join(INPUT_DIR, "sample_lineitem_*.tbl")))
    if not files:
        print("No sample files found in", INPUT_DIR)
        return

    # Process each file
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

    # --- Write output CSVs ---
    for agg, data in results.items():
        csv_path = f"rawsc_{agg}_results.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["sample_size", "mean", "variance"])
            writer.writerows(sorted(data))
        print(f"Saved results → {csv_path}")

    print("All done!")

if __name__ == "__main__":
    main()

