import numpy as np
#####                    YELLOW TAXI

# === Configuration ===
INPUT_FILE = "dirty_ytd_2024-11_12.tbl"
PRED_PASSENGER = 1.0   # passenger_count == 1

'''
=== ALL CLEAN ===
COUNT: 5059647
SUM:   138787132.590
AVG:   27.430201

=== ALL DIRTY ===
COUNT: 5650714
SUM:   196872450.280
AVG:   34.840279
'''

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


def compute_aggregates(path):
    clean_vals, dirty_vals = [], []
    clean_dups, dirty_dups = [], []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            parsed = parse_line(line)
            if parsed is None:
                continue

            (clean_total, clean_pass, dirty_total, dirty_pass, numdup) = parsed

            # Predicate: passenger_count == 1
            if clean_pass == PRED_PASSENGER:
                clean_vals.append(clean_total)
                clean_dups.append(1)     # clean lines are not duplicated in original data

            if dirty_pass == PRED_PASSENGER:
                dirty_vals.append(dirty_total)
                dirty_dups.append(numdup)  # dirty duplication factor

    if not clean_vals or not dirty_vals:
        print("No matching rows for predicate.")
        return

    clean_vals = np.array(clean_vals)
    dirty_vals = np.array(dirty_vals)
    clean_dups = np.array(clean_dups)
    dirty_dups = np.array(dirty_dups)

    # Weighted aggregates
    clean_sum = np.sum(clean_vals * clean_dups)
    dirty_sum = np.sum(dirty_vals * dirty_dups)

    clean_count = np.sum(clean_dups)
    dirty_count = np.sum(dirty_dups)

    clean_avg = clean_sum / clean_count
    dirty_avg = dirty_sum / dirty_count

    print("=== ALL CLEAN ===")
    print(f"COUNT: {clean_count:.0f}")
    print(f"SUM:   {clean_sum:.3f}")
    print(f"AVG:   {clean_avg:.6f}")
    print()
    print("=== ALL DIRTY ===")
    print(f"COUNT: {dirty_count:.0f}")
    print(f"SUM:   {dirty_sum:.3f}")
    print(f"AVG:   {dirty_avg:.6f}")


if __name__ == "__main__":
    compute_aggregates(INPUT_FILE)

