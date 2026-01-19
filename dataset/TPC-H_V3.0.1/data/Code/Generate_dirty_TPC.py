import random
import os

# === Config ===
INPUT_FILE = "lineitem.tbl"
OUTPUT_DIR = "sample/"
ALLDIRTY_FILE = "dirty_lineitem.tbl"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# OCR digit confusion mapping
OCR_CONFUSION = {
    '0': ['6', '8', '0'],
    '1': ['7', '1'],
    '2': ['5', '2'],
    '3': ['8', '9', '3'],
    '4': ['9', '4'],
    '5': ['2', '6', '5'],
    '6': ['0', '8', '6'],
    '7': ['1', '7'],
    '8': ['0', '6', '3', '8'],
    '9': ['3', '4', '9']
}

# Field indices in lineitem.tbl
QTY_IDX = 4           # l_quantity
RETURNFLAG_IDX = 8    # l_returnflag
LINESTATUS_IDX = 9    # l_linestatus

# Error probabilities
VAL_ERR_PROB = 0.30   # 30% chance for OCR quantity error
COND_ERR_PROB = 0.10  # 10% chance for condition error (returnflag)
DUP_ERR_PROB = 0.20   # 20% chance for duplication

TOT_LINE_NUMBER = 6000000 # assuming 6 million total lines
TOT_DIRTY_LINES = TOT_LINE_NUMBER * (1 + DUP_ERR_PROB)


# Sampling settings
SAMPLE_SIZES = list(range(500, 10001, 500))

def ocr_confuse(value: str) -> str:
    """Apply OCR-like digit confusion to a numeric string."""
    result = []
    for ch in value:
        if ch in OCR_CONFUSION:
            result.append(random.choice(OCR_CONFUSION[ch]))
        else:
            result.append(ch)
    return ''.join(result)

def main():
    total_lines = 0
    dirty_value_changes = 0
    duplicate_count = 0

    # Prepare sample output file handles
    sample_files = {}
    for N in SAMPLE_SIZES:
        fname = os.path.join(OUTPUT_DIR, f"sample_lineitem_{N}.tbl")
        sample_files[N] = open(fname, "w")
    
    all_dirty_file = open(ALLDIRTY_FILE, "w")

    with open(INPUT_FILE, "r", encoding="utf-8") as fin:
        for line in fin:
            if not line.strip():
                continue
            total_lines += 1
            fields = line.strip().split('|')

            clean_qty = fields[QTY_IDX]
            clean_return = fields[RETURNFLAG_IDX]
            clean_status = fields[LINESTATUS_IDX]

            # Start dirty = clean
            dirty_qty = clean_qty
            dirty_return = clean_return
            dirty_status = clean_status
            num_dup = 1
            dirty_flag = False

            # Apply OCR-like value error (30%)
            if random.random() < VAL_ERR_PROB:
                dirty_qty = ocr_confuse(clean_qty)
                if dirty_qty != clean_qty:
                    dirty_flag = True

            # Apply condition error (10%)
            if random.random() < COND_ERR_PROB:
                dirty_return = random.choice(['A', 'B', 'C', 'R', 'N', 'F'])
                dirty_flag = True

            # Duplication error (20%)
            if random.random() < DUP_ERR_PROB:
                num_dup = 2
                duplicate_count += 1

            if dirty_flag:
                dirty_value_changes += 1

            # Build the output line
            out_line = f"{clean_qty}|{clean_return}|{clean_status}|{dirty_qty}|{dirty_return}|{dirty_status}|{num_dup}\n"

            # Random sampling into sample files
            for N in SAMPLE_SIZES:
                prob = (N * num_dup) / TOT_DIRTY_LINES
                if random.random() < prob:
                    sample_files[N].write(out_line)
                    
            all_dirty_file.write(out_line)

    # Close sample files
    for f in sample_files.values():
        f.close()

    print("=== Summary ===")
    print(f"Total lines processed: {total_lines}")
    print(f"Lines with dirty value changes: {dirty_value_changes}")
    print(f"Lines with duplication: {duplicate_count}")
    print(f"Output samples written to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

