import os
import glob
import csv
import numpy as np
#####                    YELLOW TAXI

# === Configuration ===
INPUT_DIR = "sample/"
PRED_PASSENGER = 1.0   # predicate: passenger_count == 1
N = 7937540          # total population size (adjust if needed)

# === Helper ===
def parse_line(line):
    parts = line.strip().split("|")
    if len(parts) < 5:
        return None
    try:
        clean_total = float(parts[0])
        passenger = float(parts[1])
        numdup = float(parts[4])
        return clean_total, passenger, numdup
    except ValueError:
        return None


def process_sample_file(filepath):
    """Compute RawSC stats for AVG, SUM, COUNT on sample_ytd_*.tbl"""
    clean_vals = []
    preds = []
    numdups = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            parsed = parse_line(line)
            if parsed is None:
                continue
            total, passenger, numdup = parsed

            # New predicate: passenger_count == 1
            pred = float(passenger == PRED_PASSENGER)

            clean_vals.append(total)
            preds.append(pred)
            numdups.append(numdup)

    K = len(clean_vals)
    if K == 0:
        return None

    clean_vals = np.array(clean_vals)
    preds = np.array(preds)
    numdups = np.array(numdups)

    K_pred = np.sum(preds)
    if K_pred == 0:
        return None

    # Duplication rate d
    d = K / np.sum(1.0 / numdups)

    # RawSC estimators
    phi_count = preds * (N / numdups)
    phi_sum   = preds * (N * clean_vals / numdups)
    phi_avg   = preds * (d * K / K_pred) * (clean_vals / numdups)

    mean_count, var_count = np.mean(phi_count), np.var(phi_count, ddof=1)
    mean_sum,  var_sum  = np.mean(phi_sum),  np.var(phi_sum,  ddof=1)
    mean_avg,  var_avg  = np.mean(phi_avg),  np.var(phi_avg,  ddof=1)

    return {
        "K": K,
        "count": (mean_count, var_count),
        "sum": (mean_sum, var_sum),
        "avg": (mean_avg, var_avg),
    }


def main():
    results = {"count": [], "sum": [], "avg": []}

    files = sorted(glob.glob(os.path.join(INPUT_DIR, "sample_ytd_*.tbl")))
    if not files:
        print("No sample files found in", INPUT_DIR)
        return

    for file in files:
        sample_size = int(os.path.basename(file).split("_")[-1].split(".")[0])
        res = process_sample_file(file)
        if res is None:
            print(f"Skipping {file} (no matching predicate rows).")
            continue

        for agg in ["count", "sum", "avg"]:
            mean, var = res[agg]
            results[agg].append((sample_size, mean, var))

        print(f"Processed {file} ✅")

    # Write CSVs
    for agg, data in results.items():
        csv_path = f"rawsc_{agg}_results_ytd.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["sample_size", "mean", "variance"])
            writer.writerows(sorted(data))
        print(f"Saved → {csv_path}")

    print("Done.")

if __name__ == "__main__":
    main()

