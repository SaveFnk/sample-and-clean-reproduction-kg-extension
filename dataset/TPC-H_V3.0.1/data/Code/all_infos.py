import numpy as np

# === Configuration ===
INPUT_FILE = "dirty_lineitem.tbl"
PRED_RETURNFLAG = "A"
PRED_LINESTATUS = "F"

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
        return (clean_qty, clean_return, clean_status,
                dirty_qty, dirty_return, dirty_status,
                numdup)
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
            (cq, cr, cs, dq, dr, ds, numdup) = parsed

            # Predicate: returnflag='A' and linestatus='F'
            if cr == PRED_RETURNFLAG and cs == PRED_LINESTATUS:
                clean_vals.append(cq)
                clean_dups.append(1)
            if dr == PRED_RETURNFLAG and ds == PRED_LINESTATUS:
                dirty_vals.append(dq)
                dirty_dups.append(numdup)

    if not clean_vals or not dirty_vals:
        print("No matching rows for predicate.")
        return

    clean_vals, dirty_vals = np.array(clean_vals), np.array(dirty_vals)
    clean_dups, dirty_dups = np.array(clean_dups), np.array(dirty_dups)

    # Weighted aggregates (taking duplication into account)
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

