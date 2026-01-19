#!/usr/bin/env python3
import subprocess
import sys
import json
import csv
import os
import re
from glob import glob
from math import sqrt

# ============================================
# CONFIG
# ============================================

REPO_URL = "http://localhost:7200/repositories/personaldata_subset"
STATEMENTS_URL = REPO_URL + "/statements"
SAMPLES_GLOB = "clean/persondata_sample_*.ttl"

CSV_COUNT = "normsc_count_results.csv"
CSV_SUM   = "normsc_sum_results.csv"
CSV_AVG   = "normsc_avg_results.csv"

DIRTY_POP_SIZE_N = 1254428

ALLDIRTY_COUNT = 735646
ALLDIRTY_SUM   = 1667366188
ALLDIRTY_AVG   = ALLDIRTY_SUM / ALLDIRTY_COUNT

Z_VALUE = 1.96

DELETE_QUERY = "DELETE WHERE { ?s ?p ?o }"

# ============================================
# SPARQL QUERIES
# ============================================

META_QUERY = """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ex: <http://example.org/ontology/>

SELECT
  (COUNT(?person) AS ?K)
  (SUM(1.0/xsd:double(?numdirty)) AS ?Kprime)
  (SUM(IF(BOUND(?cdate),1,0)) AS ?Kp_clean)
  (SUM(IF(BOUND(?ddate),1,0)) AS ?Kp_dirty)
WHERE {
  ?person a foaf:Person ;
          ex:numdirty ?numdirty .
  OPTIONAL { ?person dbo:birthDate ?cdate . }
  OPTIONAL { ?person ex:birthDate_dirty ?ddate . }
}
"""

TUPLES_QUERY = """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ex: <http://example.org/ontology/>

SELECT
  ?numdirty
  (IF(BOUND(?cdate),1,0) AS ?pred_clean)
  (IF(BOUND(?ddate),1,0) AS ?pred_dirty)
  (IF(BOUND(?cdate),YEAR(xsd:date(?cdate)),0) AS ?year_clean)
  (IF(BOUND(?ddate),YEAR(xsd:date(?ddate)),0) AS ?year_dirty)
WHERE {
  ?person a foaf:Person ;
          ex:numdirty ?numdirty .
  OPTIONAL { ?person dbo:birthDate ?cdate . }
  OPTIONAL { ?person ex:birthDate_dirty ?ddate . }
}
"""

# ============================================
# UTIL FUNCTIONS
# ============================================

def import_file(path):
    subprocess.run([
        "curl","-X","POST",
        "-H","Content-Type: text/turtle",
        "--data-binary", f"@{path}",
        STATEMENTS_URL
    ], check=True)

def run_query(q):
    p = subprocess.Popen(
        ["curl","-X","POST",
         "-H","Content-Type: application/sparql-query",
         "-H","Accept: application/sparql-results+json",
         "--data-binary","@-", REPO_URL],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    out,_ = p.communicate(q)
    return json.loads(out)

def delete_all():
    subprocess.Popen(
        ["curl","-X","POST","-H","Content-Type: application/sparql-update",
         "--data-binary","@-", STATEMENTS_URL],
        stdin=subprocess.PIPE,
        text=True
    ).communicate(DELETE_QUERY)

def extract_size(path):
    m = re.search(r"(\d+)\.ttl$", path)
    return int(m.group(1))

# ============================================
# MAIN LOGIC
# ============================================

def main():

    sample_files = sorted(glob(SAMPLES_GLOB), key=extract_size)

    fout_count = csv.writer(open(CSV_COUNT,"w"))
    fout_sum   = csv.writer(open(CSV_SUM,"w"))
    fout_avg   = csv.writer(open(CSV_AVG,"w"))

    # Add CI fields
    fout_count.writerow(["sample_size","normsc_count","ci_count"])
    fout_sum.writerow(["sample_size","normsc_sum","ci_sum"])
    fout_avg.writerow(["sample_size","normsc_avg","ci_avg"])

    for fp in sample_files:
        size = extract_size(fp)

        print("\n=== SAMPLE", size, "===")

        delete_all()
        import_file(fp)

        meta = run_query(META_QUERY)["results"]["bindings"][0]
        K = float(meta["K"]["value"])
        Kprime = float(meta["Kprime"]["value"])
        Kp_clean = float(meta["Kp_clean"]["value"])
        Kp_dirty = float(meta["Kp_dirty"]["value"])

        d = K / Kprime

        print("K =", K, "K' =", Kprime, "Kp_clean =", Kp_clean, "Kp_dirty =", Kp_dirty)

        res = run_query(TUPLES_QUERY)
        rows = res["results"]["bindings"]

        q_count = []
        q_sum   = []
        q_avg   = []

        for r in rows:
            nd = float(r["numdirty"]["value"])
            m = int(nd)

            pred_clean = float(r.get("pred_clean", {}).get("value", "0"))
            pred_dirty = float(r.get("pred_dirty", {}).get("value", "0"))
            yc = float(r.get("year_clean", {}).get("value", "0"))
            yd = float(r.get("year_dirty", {}).get("value", "0"))

            phi_d_count = pred_dirty * DIRTY_POP_SIZE_N
            phi_d_sum   = pred_dirty * DIRTY_POP_SIZE_N * yd
            phi_d_avg   = pred_dirty * (K / Kp_dirty) * yd if Kp_dirty > 0 else 0.0

            phi_c_count = pred_clean * (DIRTY_POP_SIZE_N / nd)
            phi_c_sum   = pred_clean * (DIRTY_POP_SIZE_N * yc / nd)
            phi_c_avg   = pred_clean * (d * K / Kp_clean) * (yc / nd) if Kp_clean > 0 else 0.0

            diff_count = phi_d_count - phi_c_count
            diff_sum   = phi_d_sum   - phi_c_sum
            diff_avg   = phi_d_avg   - phi_c_avg

            q_count.extend([diff_count] * m)
            q_sum.extend([diff_sum] * m)
            q_avg.append(diff_avg)

        # ---- MEAN ----
        mean_qc = sum(q_count) / len(q_count)
        mean_qs = sum(q_sum) / len(q_sum)
        mean_qa = sum(q_avg) / len(q_avg)

        # ---- NORM RESULTS ----
        norm_count = ALLDIRTY_COUNT - mean_qc
        norm_sum   = ALLDIRTY_SUM   - mean_qs
        norm_avg   = ALLDIRTY_AVG   - mean_qa

        print("NormalizedSC COUNT =", norm_count)
        print("NormalizedSC SUM   =", norm_sum)
        print("NormalizedSC AVG   =", norm_avg)

        # -----------------------------------
        # CONFIDENCE INTERVALS (SampleClean)
        # CI = Z * stddev(q) / sqrt(K)
        # -----------------------------------

        def stddev(arr, mean):
            return sqrt(sum((x-mean)**2 for x in arr) / (len(arr)-1)) if len(arr) > 1 else 0.0

        std_qc = stddev(q_count, mean_qc)
        std_qs = stddev(q_sum, mean_qs)
        std_qa = stddev(q_avg, mean_qa)

        ci_count = Z_VALUE * std_qc / sqrt(K)
        ci_sum   = Z_VALUE * std_qs / sqrt(K)
        ci_avg   = Z_VALUE * std_qa / sqrt(K)

        fout_count.writerow([size, norm_count, ci_count])
        fout_sum.writerow([size, norm_sum, ci_sum])
        fout_avg.writerow([size, norm_avg, ci_avg])


if __name__ == "__main__":
    main()

