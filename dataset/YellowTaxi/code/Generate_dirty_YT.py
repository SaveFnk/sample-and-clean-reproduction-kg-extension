import random
import os

# === Config ===
INPUT_FILE = "ytd_2024-11_12.tbl"
OUTPUT_DIR = "sample/"
ALLDIRTY_FILE = "dirty_ytd_2024-11_12.tbl"

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

# Field indices for new dataset
# clean_total_amount | clean_passenger_count | dirty_total_amount | dirty_passenger_count | num_dup

PASSENGER_IDX = 2
TOTAL_IDX = 4     # total_amount is the quantity-like attribute

# Error probabilities
VAL_ERR_PROB = 0.30   # OCR value confusion on total_amount
COND_ERR_PROB = 0.10  # passenger_count modification
DUP_ERR_PROB = 0.20   # duplication

# Approx dataset size (adjust if known)
TOT_LINE_NUMBER = 6614775
TOT_DIRTY_LINES = TOT_LINE_NUMBER * (1 + DUP_ERR_PROB)

'''
Total lines processed: 6614775
Lines with dirty value changes: 2358194
Lines with duplication: 1322765
Output samples written to: sample/
'''

# Sampling settings
SAMPLE_SIZES = list(range(500, 10001, 500))

def ocr_confuse(value: str) -> str:
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

    sample_files = {}
    for N in SAMPLE_SIZES:
        fname = os.path.join(OUTPUT_DIR, f"sample_ytd_{N}.tbl")
        sample_files[N] = open(fname, "w")
    
    all_dirty_file = open(ALLDIRTY_FILE, "w")

    with open(INPUT_FILE, "r", encoding="utf-8") as fin:
        for line in fin:
            if not line.strip():
                continue
            total_lines += 1
            fields = line.strip().split('|')

            clean_total = fields[TOTAL_IDX]
            clean_passenger = fields[PASSENGER_IDX]

            dirty_total = clean_total
            dirty_passenger = clean_passenger
            num_dup = 1
            dirty_flag = False

            # Apply OCR confusion to total_amount
            if random.random() < VAL_ERR_PROB:
                dirty_total = ocr_confuse(clean_total)
                if dirty_total != clean_total:
                    dirty_flag = True

            # Apply passenger_count condition rule
            if random.random() < COND_ERR_PROB:
                p = float(clean_passenger)
                if p == 1:
                    dirty_passenger = "2"
                else:
                    dirty_passenger = "1"
                dirty_flag = True

            # Duplication error
            if random.random() < DUP_ERR_PROB:
                num_dup = 2
                duplicate_count += 1

            if dirty_flag:
                dirty_value_changes += 1

            out_line = f"{clean_total}|{clean_passenger}|{dirty_total}|{dirty_passenger}|{num_dup}\n"

            # Sampling
            for N in SAMPLE_SIZES:
                prob = (N * num_dup) / TOT_DIRTY_LINES
                if random.random() < prob:
                    sample_files[N].write(out_line)

            all_dirty_file.write(out_line)

    for f in sample_files.values():
        f.close()

    print("=== Summary ===")
    print(f"Total lines processed: {total_lines}")
    print(f"Lines with dirty value changes: {dirty_value_changes}")
    print(f"Lines with duplication: {duplicate_count}")
    print(f"Output samples written to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

