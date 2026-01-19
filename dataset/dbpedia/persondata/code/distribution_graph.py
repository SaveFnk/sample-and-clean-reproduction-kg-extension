import re
import matplotlib.pyplot as plt
import numpy as np

dirty_full_file = "persondata_dirty_full.ttl"

# Patterns
clean_date_pattern  = re.compile(r'<http://dbpedia.org/ontology/birthDate>\s*"(\d{4})')
dirty_date_pattern  = re.compile(r'<http://example.org/ontology/birthDate_dirty>\s*"(\d{4})')
numdirty_pattern     = re.compile(r'<http://example.org/ontology/numdirty>\s*"(\d+)"')


def extract_years_from_dirty_full(ttl_path):
    clean_years = []
    dirty_years = []

    current_subject = None
    current_clean = None
    current_dirty = None
    current_numdirty = 1

    with open(ttl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Extract subject URI
            subject = line.split(" ")[0]

            # New subject block begins
            if current_subject is None:
                current_subject = subject

            elif subject != current_subject:
                # Save previous subject data
                if current_clean is not None:
                    clean_years.extend([current_clean] * current_numdirty)
                    dirty_years.extend([current_dirty] * current_numdirty)

                # Reset for new subject
                current_subject = subject
                current_clean = None
                current_dirty = None
                current_numdirty = 1

            # Clean birthDate
            m = clean_date_pattern.search(line)
            if m:
                current_clean = int(m.group(1))

            # Dirty birthDate
            m = dirty_date_pattern.search(line)
            if m:
                current_dirty = int(m.group(1))

            # numdirty
            m = numdirty_pattern.search(line)
            if m:
                current_numdirty = int(m.group(1))

        # Save LAST subject
        if current_clean is not None:
            clean_years.extend([current_clean] * 1)
            dirty_years.extend([current_dirty] * current_numdirty)

    return clean_years, dirty_years


# ---- Load years from new full-dirty dataset ----
clean_years, dirty_years = extract_years_from_dirty_full(dirty_full_file)

# --- Statistics ---
clean_mean = np.mean(clean_years)
dirty_mean = np.mean(dirty_years)
clean_std = np.std(clean_years)
dirty_std = np.std(dirty_years)

# Plotting
xmin = 0
xmax = 8000
x_margin = (xmax - xmin) * 0.05
x_limits = (xmin - x_margin, xmax + x_margin)

plt.figure(figsize=(12, 6))
bins = np.linspace(x_limits[0], x_limits[1], 200)

plt.hist(dirty_years, bins=bins, alpha=0.5, color="orange", label="Dirty", density=False)
plt.hist(clean_years, bins=bins, alpha=0.5, color="steelblue", label="Clean", density=False)

plt.axvline(clean_mean, color="blue", linestyle="--", linewidth=1.5, label=f"Clean mean = {clean_mean:.1f}")
plt.axvline(dirty_mean, color="darkorange", linestyle="--", linewidth=1.5, label=f"Dirty mean = {dirty_mean:.1f}")

ylim = plt.ylim()
plt.text(clean_mean, ylim[1]*0.9, f"{clean_mean:.1f}", color="blue", fontsize=9)
plt.text(dirty_mean, ylim[1]*0.8, f"{dirty_mean:.1f}", color="darkorange", fontsize=9)

plt.xlim(x_limits)
plt.xlabel("Birth year")
plt.ylabel("Number of people")
plt.title("Birth Year Distribution: Clean vs Dirty Data (Weighted by numdirty)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("graph/distribution_persondata_birth_year2.png", dpi=200)
plt.show()

# --- Print stats ---
print(f"Clean mean: {clean_mean:.2f}, std: {clean_std:.2f}, n={len(clean_years)}")
print(f"Dirty mean: {dirty_mean:.2f}, std: {dirty_std:.2f}, n={len(dirty_years)}")
print(f"X-axis range: {x_limits}")

