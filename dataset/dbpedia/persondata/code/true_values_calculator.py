#!/usr/bin/env python3
import re

DIRTY_FILE = "persondata_dirty_full.ttl"

print("Reading dirty full dataset...")

# Regex to extract subject and year safely
SUBJ_RE = re.compile(r"^<([^>]+)>")
YEAR_RE = re.compile(r'"(\d{4})')  # only extract the first 4-digit year

# Storage for all subjects
birth_clean = {}      # subject → clean birth year (int)
birth_dirty = {}      # subject → dirty birth year (int)
numdup = {}           # subject → numdirty (int)

with open(DIRTY_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or not line.startswith("<"):
            continue

        m = SUBJ_RE.match(line)
        if not m:
            continue

        subj = m.group(1)

        # ------------ numdirty ------------
        if "numdirty" in line:
            n = YEAR_RE.search(line)
            try:
                numdir = int(line.split('"')[1])
                numdup[subj] = numdir
                
            except:
                numdup[subj] = 1

        # ------------ clean birthDate ------------
        elif "dbpedia.org/ontology/birthDate" in line and "birthDate_dirty" not in line:
            y = YEAR_RE.search(line)
            if y:
                birth_clean[subj] = int(y.group(1))

        # ------------ dirty birthDate ------------
        elif "example.org/ontology/birthDate_dirty" in line:
            y = YEAR_RE.search(line)
            if y:
                birth_dirty[subj] = int(y.group(1))

print("Finished reading. Computing statistics...\n")

# Ensure all subjects have a numdup (default = 1)
for s in set(list(birth_clean.keys()) + list(birth_dirty.keys())):
    if s not in numdup:
        numdup[s] = 1

# --------------------------
# SUBJECT-LEVEL STATISTICS
# --------------------------

clean_years = [birth_clean[s] for s in birth_clean]
dirty_years = [birth_dirty[s] for s in birth_dirty]

count_clean_subject = len(clean_years)
count_dirty_subject = len(dirty_years)

sum_clean_subject = sum(clean_years)
sum_dirty_subject = sum(dirty_years)

avg_clean_subject = sum_clean_subject / count_clean_subject if count_clean_subject else 0
avg_dirty_subject = sum_dirty_subject / count_dirty_subject if count_dirty_subject else 0


# -------------------------------
# POPULATION-LEVEL STATISTICS
# Each subject counts numdup[s] times
# -------------------------------

count_clean_pop = 0
sum_clean_pop = 0

count_dirty_pop = 0
sum_dirty_pop = 0

for s, year in birth_clean.items():
    nd = numdup.get(s, 1)
    count_clean_pop += nd
    sum_clean_pop += year * nd

for s, year in birth_dirty.items():
    nd = numdup.get(s, 1)
    count_dirty_pop += nd
    sum_dirty_pop += year * nd

avg_clean_pop = sum_clean_pop / count_clean_pop if count_clean_pop else 0
avg_dirty_pop = sum_dirty_pop / count_dirty_pop if count_dirty_pop else 0


# -------------------------------
# REPORT
# -------------------------------
print("====================== FINAL RESULTS ======================")

print(f"Total subjects:           {sum(numdup.values())}\n")

print("---- SUBJECT-LEVEL CLEAN ----")
print(f"COUNT_clean_subject = {count_clean_subject}")
print(f"SUM_clean_subject   = {sum_clean_subject}")
print(f"AVG_clean_subject   = {avg_clean_subject}\n")

print("---- SUBJECT-LEVEL DIRTY ----")
print(f"COUNT_dirty_subject = {count_dirty_subject}")
print(f"SUM_dirty_subject   = {sum_dirty_subject}")
print(f"AVG_dirty_subject   = {avg_dirty_subject}\n")

print("---- POPULATION-LEVEL CLEAN ----")
print(f"COUNT_clean_population = {count_clean_pop}")
print(f"SUM_clean_population   = {sum_clean_pop}")
print(f"AVG_clean_population   = {avg_clean_pop}\n")

print("---- POPULATION-LEVEL DIRTY ----")
print(f"COUNT_dirty_population = {count_dirty_pop}")
print(f"SUM_dirty_population   = {sum_dirty_pop}")
print(f"AVG_dirty_population   = {avg_dirty_pop}\n")

print("---- MISSING ----")
print(f"Missing clean birthdates: {len(numdup) - count_clean_subject}")
print(f"Missing dirty birthdates: {len(numdup) - count_dirty_subject}")

