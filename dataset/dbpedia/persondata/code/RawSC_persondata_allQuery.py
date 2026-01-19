#!/usr/bin/env python3
import subprocess
import sys
import json
import csv
import os
import re
from glob import glob
from math import sqrt

# ---------- CONFIG ----------

REPO_URL = "http://localhost:7200/repositories/personaldata_subset"
STATEMENTS_URL = REPO_URL + "/statements"

SAMPLES_GLOB = "clean/persondata_sample_*.ttl"

CSV_AVG   = "rawsc_avg_results.csv"
CSV_SUM   = "rawsc_sum_results.csv"
CSV_COUNT = "rawsc_count_results.csv"

# 95% confidence interval z-value
Z_VALUE = 1.96

# IMPORTANT: size of the FULL dirty population (including duplicates)
DIRTY_POP_SIZE_N = 1021408

DELETE_QUERY = "DELETE WHERE { ?s ?p ?o }"

# ---------- SPARQL QUERIES ----------

# 1) Meta query: K, K', Kp
RAWSC_META_QUERY = """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ex: <http://example.org/ontology/>

SELECT
  (COUNT(?person) AS ?K)
  (SUM(1.0 / xsd:double(?numdirty)) AS ?Kprime)
  (SUM(IF(BOUND(?date), 1, 0)) AS ?Kp)
WHERE {
  ?person a foaf:Person ;
          ex:numdirty ?numdirty .
  OPTIONAL { ?person dbo:birthDate ?date . }
}
"""

# 2) Per-tuple query: numdirty, predicate (=has birthDate), birth year
RAWSC_TUPLES_QUERY = """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ex: <http://example.org/ontology/>

SELECT
  ?numdirty
  (IF(BOUND(?date), 1, 0) AS ?pred)
  (IF(BOUND(?date), YEAR(xsd:date(?date)), 0) AS ?year)
WHERE {
  ?person a foaf:Person ;
          ex:numdirty ?numdirty .
  OPTIONAL { ?person dbo:birthDate ?date . }
}
"""

# ---------- HELPER FUNCTIONS ----------

def import_file(filepath: str):
    print(f"Importing file {filepath}...")
    result = subprocess.run(
        [
            "curl",
            "-X", "POST",
            "-H", "Content-Type: text/turtle",
            "--data-binary", f"@{filepath}",
            STATEMENTS_URL,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Import failed:", result.stderr)
        sys.exit(1)
    print("Import OK")

def run_query(query: str):
    """Run a SPARQL query string and return JSON result."""
    proc = subprocess.Popen(
        [
            "curl",
            "-X", "POST",
            "-H", "Content-Type: application/sparql-query",
            "-H", "Accept: application/sparql-results+json",
            "--data-binary", "@-",
            REPO_URL,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = proc.communicate(query)
    if proc.returncode != 0:
        print("Query failed:", err)
        sys.exit(1)
    return json.loads(out)

def delete_all_data():
    print("Clearing repository...")
    proc = subprocess.Popen(
        [
            "curl",
            "-X", "POST",
            "-H", "Content-Type: application/sparql-update",
            "--data-binary", "@-",
            STATEMENTS_URL,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = proc.communicate(DELETE_QUERY)
    if proc.returncode != 0:
        print("Delete query failed:", err)
        sys.exit(1)
    print("Repo cleared.")

def extract_sample_size(path: str) -> int:
    """
    Extract N from '...persondata_sample_<N>.ttl'.
    Returns int(N), or -1 if it cannot parse.
    """
    base = os.path.basename(path)
    m = re.search(r"persondata_sample_(\d+)\.ttl", base)
    if m:
        return int(m.group(1))
    return -1

def mean_and_var(values):
    """Return (mean, sample_variance) for a list of floats."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mu = sum(values) / n
    if n > 1:
        var = sum((x - mu) ** 2 for x in values) / (n - 1)
    else:
        var = 0.0
    return mu, var

def ci_from_mean_var(mu, var, K, N, z=Z_VALUE):
    """
    Compute CI = mu ± z * sqrt(var / K) * fpc,
    where fpc = sqrt((N - K) / (N - 1)) is the finite population correction.
    """
    if K <= 0:
        return mu, mu
    # standard error
    se = sqrt(var / K)
    # finite population correction
    if N > 1 and K < N:
        fpc = sqrt((N - K) / (N - 1))
    else:
        fpc = 1.0
    half_width = z * se * fpc
    return mu - half_width, mu + half_width

# ---------- MAIN ----------

def main():
    # Collect sample files and sort by sample size
    sample_files = sorted(glob(SAMPLES_GLOB), key=extract_sample_size)
    if not sample_files:
        print(f"No sample files found matching {SAMPLES_GLOB}")
        sys.exit(1)

    # Prepare CSV writers
    avg_exists   = os.path.isfile(CSV_AVG)
    sum_exists   = os.path.isfile(CSV_SUM)
    count_exists = os.path.isfile(CSV_COUNT)

    avg_f   = open(CSV_AVG,   "a", newline="", encoding="utf-8")
    sum_f   = open(CSV_SUM,   "a", newline="", encoding="utf-8")
    count_f = open(CSV_COUNT, "a", newline="", encoding="utf-8")

    avg_writer   = csv.writer(avg_f)
    sum_writer   = csv.writer(sum_f)
    count_writer = csv.writer(count_f)

    if not avg_exists:
        avg_writer.writerow(["sample_size", "mu_avg", "ci_low", "ci_high"])
    if not sum_exists:
        sum_writer.writerow(["sample_size", "mu_sum", "ci_low", "ci_high"])
    if not count_exists:
        count_writer.writerow(["sample_size", "mu_count", "ci_low", "ci_high"])

    try:
        for filepath in sample_files:
            sample_size = extract_sample_size(filepath)
            print("\n================================")
            print(f"=== SAMPLE {sample_size} ===")
            print("================================")

            # 1. Clear repo and import this sample
            delete_all_data()
            import_file(filepath)

            # 2. META: get K, K', Kp
            meta_res = run_query(RAWSC_META_QUERY)
            b = meta_res["results"]["bindings"][0]

            K      = float(b["K"]["value"])      if "K"      in b else 0.0
            Kprime = float(b["Kprime"]["value"]) if "Kprime" in b else 0.0
            Kp     = float(b["Kp"]["value"])     if "Kp"     in b else 0.0

            if K == 0:
                print("K = 0, skipping sample.")
                continue

            # duplication rate d = K / K'
            d = K / Kprime if Kprime > 0 else 1.0

            print(f"K (sample size):        {K}")
            print(f"K' (Σ 1/numdirty):      {Kprime}")
            print(f"Kp (# with birthDate):  {Kp}")
            print(f"d (duplication rate):   {d}")
            if Kp > 0:
                print(f"d * K / Kp (for AVG φ): {d * K / Kp}")

            # 3. PER-TUPLE: get numdirty, predicate, year
            tuples_res = run_query(RAWSC_TUPLES_QUERY)
            bindings = tuples_res["results"]["bindings"]

            phi_count = []
            phi_sum   = []
            phi_avg   = []

            for row in bindings:
                # numdirty must always exist
                numdirty = float(row["numdirty"]["value"])
                if numdirty == 0:
                    continue

                # predicate 0/1 and year (0 if no date)
                pred = float(row.get("pred", {}).get("value", 0.0))
                year = float(row.get("year", {}).get("value", 0.0))

                # φ_clean for COUNT and SUM (RawSC, Table 1)
                phi_c = pred * DIRTY_POP_SIZE_N / numdirty
                phi_s = pred * DIRTY_POP_SIZE_N * year / numdirty

                # φ_clean for AVG
                if Kp > 0:
                    phi_a = pred * (d * K / Kp) * year / numdirty
                else:
                    phi_a = 0.0

                phi_count.append(phi_c)
                phi_sum.append(phi_s)
                phi_avg.append(phi_a)

            # Sanity check: should have one φ per sampled tuple
            if len(phi_count) != int(K):
                print(
                    f"WARNING: K={K} but got {len(phi_count)} tuples "
                    f"from RAWSC_TUPLES_QUERY"
                )

            # 4. Compute means, variances, and CIs from φ_clean values

            mu_count, var_count = mean_and_var(phi_count)
            mu_sum,   var_sum   = mean_and_var(phi_sum)
            mu_avg,   var_avg   = mean_and_var(phi_avg)

            ci_count_low, ci_count_high = ci_from_mean_var(
                mu_count, var_count, K, DIRTY_POP_SIZE_N
            )
            ci_sum_low, ci_sum_high = ci_from_mean_var(
                mu_sum, var_sum, K, DIRTY_POP_SIZE_N
            )
            ci_avg_low, ci_avg_high = ci_from_mean_var(
                mu_avg, var_avg, K, DIRTY_POP_SIZE_N
            )

            print(f"RawSC COUNT   = {mu_count}")
            print(f"  CI COUNT    = [{ci_count_low}, {ci_count_high}]")
            print(f"  Var COUNT   = {var_count}")

            print(f"RawSC SUM     = {mu_sum}")
            print(f"  CI SUM      = [{ci_sum_low}, {ci_sum_high}]")
            print(f"  Var SUM     = {var_sum}")

            print(f"RawSC AVG     = {mu_avg}")
            print(f"  CI AVG      = [{ci_avg_low}, {ci_avg_high}]")
            print(f"  Var AVG     = {var_avg}")

            # 5. Write to CSVs
            count_writer.writerow([sample_size, mu_count, ci_count_low, ci_count_high])
            sum_writer.writerow([sample_size,   mu_sum,   ci_sum_low,   ci_sum_high])
            avg_writer.writerow([sample_size,   mu_avg,   ci_avg_low,   ci_avg_high])

        # Optionally clear repo at the end
        delete_all_data()

    finally:
        avg_f.close()
        sum_f.close()
        count_f.close()

if __name__ == "__main__":
    main()

