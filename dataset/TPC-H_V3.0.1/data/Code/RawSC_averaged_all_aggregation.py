import os
import glob
import csv
import numpy as np

# === Configuration ===
INPUT_DIR = "sample/"
PRED_RETURNFLAG = "A"
PRED_LINESTATUS = "F"

N = 7201871  # total population size 


# === NEW: split dataset into 5 subsets ===
def split_into_subsets(lines, num_parts=5):
    chunk_size = len(lines) // num_parts
    subsets = []
    for i in range(num_parts):
        start = i * chunk_size
        # last chunk gets the remainder
        end = (i + 1) * chunk_size if i < num_parts - 1 else len(lines)
        subsets.append(lines[start:end])
    return subsets


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


# === MODIFIED: now process SAMPLE *SUBSET* instead of file ===
def process_sample_subset(lines):
    clean_vals = []
    preds = []
    numdups = []

    for line in lines:
        if not line.strip():
            continue
        parsed = parse_line(line)
        if parsed is None:
            continue
        qty, returnflag, linestatus, numdup = parsed

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

    K_pred = np.sum(preds)
    if K_pred == 0:
        return None

    # duplication correction
    d = K / np.sum(1.0 / numdups)

    # φ_clean for each aggregate
    phi_count = preds * (N / numdups)
    phi_sum   = preds * (N * clean_vals / numdups)
    phi_avg   = preds * (d * K / K_pred) * (clean_vals / numdups)

    return {
        "count": np.mean(phi_count),
        "sum": np.mean(phi_sum),
        "avg": np.mean(phi_avg),
    }


def main():
    results = {"count": [], "sum": [], "avg": []}

    files = sorted(glob.glob(os.path.join(INPUT_DIR, "sample_lineitem_*.tbl")))
    if not files:
        print("No sample files found in", INPUT_DIR)
        return

    for file in files:
        sample_size = int(os.path.basename(file).split("_")[-1].split(".")[0])

        # === NEW: Read file once ===
        with open(file, "r", encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]

        # === NEW: Split into 5 subsets ===
        subsets = split_into_subsets(lines, num_parts=5)

        subset_means = {"count": [], "sum": [], "avg": []}

        # === NEW: Run RawSC on each of the 5 subsets ===
        for idx, subset in enumerate(subsets):
            res = process_sample_subset(subset)
            if res is None:
                print(f"Subset {idx+1}/5 of {file} produced no valid result.")
                continue

            for agg in ["count", "sum", "avg"]:
                subset_means[agg].append(res[agg])

        # === NEW: Average the 5 subset results ===
        for agg in ["count", "sum", "avg"]:
            if subset_means[agg]:
                avg_est = np.mean(subset_means[agg])
                var_est = np.var(subset_means[agg], ddof=1) if len(subset_means[agg]) > 1 else 0
                results[agg].append((sample_size, avg_est, var_est))

        print(f"Processed {file} with 5-subset RawSC ✅")

    # === Save CSVs ===
    for agg, data in results.items():
        csv_path = f"rawsc_averaged_{agg}_results.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["sample_size", "mean", "variance"])
            writer.writerows(sorted(data))

        print(f"Saved → {csv_path}")

    print("All done!")


if __name__ == "__main__":
    main()

