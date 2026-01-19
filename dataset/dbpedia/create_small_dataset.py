from rdflib import Graph

INPUT_FILE = "citations_lang=en_data.ttl"
OUTPUT_FILE = "sample_citations.ttl"
MAX_TRIPLES = 4000000

g = Graph()
print("Parsing large TTL file...")
g.parse(INPUT_FILE, format="turtle")

print(f"Extracting first {MAX_TRIPLES} triples...")
g_small = Graph()

for i, triple in enumerate(g):
    if i >= MAX_TRIPLES:
        break
    g_small.add(triple)

print(f"Writing to {OUTPUT_FILE}...")
g_small.serialize(destination=OUTPUT_FILE, format="turtle")
print("Done.")
