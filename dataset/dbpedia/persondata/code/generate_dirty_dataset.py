import random

'''
======= DATASET GENERATION STATS =======
Total subjects processed:          1045474
Subjects with birthDate:           615087
Dirty birthDates modified:         177085
Dirty birthDates left unchanged:   438002
Subjects marked as duplicates:     208954
Total triples in full dirty file:  8330630
========================================
'''

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

input_file = "persondata_en.ttl"
TOTAL_ENTRIES = 1254428
N_values = range(500, 10001, 500)

sample_files_clean = {}
sample_files_stats = {}

# NEW: full dirty output file
dirty_full_file = open("persondata_dirty_full.ttl", "w", encoding="utf-8")

# Create sample output files
for N in N_values:
    sample_files_clean[N] = open(f"clean/persondata_sample_{N}.ttl", "w", encoding="utf-8")
    sample_files_stats[N] = open(f"stats/persondata_sample_{N}.txt", "w", encoding="utf-8")

# =============================
# Global Statistics Counters
# =============================
total_subjects = 0
subjects_with_birthdate = 0
dirty_modified = 0
dirty_same_as_clean = 0
duplicate_subjects = 0
total_triples_full_dirty = 0


# ----------------------------------------------------
# ALWAYS produce (clean_date, dirty_date)
# dirty_date = clean_date 70% of time
# dirty_date = modified date 30% of time
# ----------------------------------------------------
def modify_birth_date(triple, trigger_prob=0.3, per_digit_prob=0.5):

    if "birthDate" not in triple:
        return None, None

    parts = triple.split('"')
    if len(parts) < 2:
        return None, None

    clean_date = parts[1]
    if len(clean_date) < 4:
        return clean_date, clean_date

    year = clean_date[:4]
    rest = clean_date[4:]

    # 70% of time → dirty = clean
    if random.random() >= trigger_prob:
        return clean_date, clean_date

    # Modify the year (4 digits)
    new_year = []
    changed = False
    i=0
    for d in year:
        if d.isdigit():
            if i==0 and random.random() > per_digit_prob:
                new_year.append(d)
            else:
                new_year.append(random.choice(OCR_CONFUSION[d]))
                changed = True
        else:
            new_year.append(d)
        i=1

    if not changed:
        return clean_date, clean_date

    dirty_date = "".join(new_year) + rest
    return clean_date, dirty_date


# ----------------------------------------------------
# Process one subject
# ----------------------------------------------------
def process(triples):
    global total_subjects, subjects_with_birthdate
    global dirty_modified, dirty_same_as_clean
    global duplicate_subjects, total_triples_full_dirty

    subject = triples[0].split(" ")[0]
    total_subjects += 1

    # Determine sample membership
    included_sets = []
    for N in N_values:
        if random.random() < (N / TOTAL_ENTRIES):
            included_sets.append(N)

    # Always determine clean/dirty birthDate if exists
    clean_birthdate = None
    dirty_birthdate = None

    for t in triples:
        c, d = modify_birth_date(t)
        if c is not None:
            clean_birthdate = c
            dirty_birthdate = d
            subjects_with_birthdate += 1

            if c == d:
                dirty_same_as_clean += 1
            else:
                dirty_modified += 1
            break

    # Duplication probability
    duplicate = (random.random() < 0.2)
    numdirty_val = 2 if duplicate else 1

    if duplicate:
        duplicate_subjects += 1

    # ------------------------------------------------
    # ALWAYS WRITE to full dirty file
    # ------------------------------------------------
    # 1. Clean triples
    dirty_full_file.write("\n".join(triples) + "\n")
    total_triples_full_dirty += len(triples)

    # 2. Dirty birthDate triple (if subject has birthday)
    if dirty_birthdate is not None:
        dirty_full_file.write(
            f'{subject} <http://example.org/ontology/birthDate_dirty> '
            f'"{dirty_birthdate}"^^<http://www.w3.org/2001/XMLSchema#date> .\n'
        )
        total_triples_full_dirty += 1

    # 3. numdirty triple
    dirty_full_file.write(
        f'{subject} <http://example.org/ontology/numdirty> '
        f'"{numdirty_val}"^^<http://www.w3.org/2001/XMLSchema#integer> .\n'
    )
    total_triples_full_dirty += 1

    # ------------------------------------------------
    # WRITE into each sample file
    # ------------------------------------------------
    for N in included_sets:

        # Clean triples
        sample_files_clean[N].write("\n".join(triples) + "\n")

        # Dirty birthDate triple
        if dirty_birthdate is not None:
            sample_files_clean[N].write(
                f'{subject} <http://example.org/ontology/birthDate_dirty> '
                f'"{dirty_birthdate}"^^<http://www.w3.org/2001/XMLSchema#date> .\n'
            )

        # numdirty triple
        sample_files_clean[N].write(
            f'{subject} <http://example.org/ontology/numdirty> '
            f'"{numdirty_val}"^^<http://www.w3.org/2001/XMLSchema#integer> .\n'
        )

        # Stats: clean|dirty
        if clean_birthdate is not None:
            sample_files_stats[N].write(clean_birthdate + "|" + dirty_birthdate + "\n")
        else:
            sample_files_stats[N].write("0|0\n")


# ----------------------------------------------------
# Loader (iterate subject blocks)
# ----------------------------------------------------
def load_persons(filepath):
    current_subject = None
    bucket = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            subj = line.split(" ")[0]

            if subj != current_subject:
                if bucket:
                    process(bucket)
                bucket = [line]
                current_subject = subj
            else:
                bucket.append(line)

    if bucket:
        process(bucket)


# ----------------------------------------------------
# Main
# ----------------------------------------------------
if __name__ == "__main__":
    print("Processing...")
    load_persons(input_file)

    for f in sample_files_clean.values():
        f.close()
    for f in sample_files_stats.values():
        f.close()
    dirty_full_file.close()

    print("\n======= DATASET GENERATION STATS =======")
    print(f"Total subjects processed:          {total_subjects}")
    print(f"Subjects with birthDate:           {subjects_with_birthdate}")
    print(f"Dirty birthDates modified:         {dirty_modified}")
    print(f"Dirty birthDates left unchanged:   {dirty_same_as_clean}")
    print(f"Subjects marked as duplicates:     {duplicate_subjects}")
    print(f"Total triples in full dirty file:  {total_triples_full_dirty}")
    print("========================================\n")

    print("Done.")

