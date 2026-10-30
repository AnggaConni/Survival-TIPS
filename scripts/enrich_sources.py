from __future__ import annotations
from .common import ROOT, now_iso, read_json, write_json
from .source_quality import annotate_source

def main():
    payload = read_json(ROOT / "data" / "sources.json", {"schema_version": "1.0", "sources": []})
    sources = [annotate_source(source) for source in payload.get("sources", [])]
    payload["schema_version"] = "1.1"
    payload["generated_at"] = now_iso()
    payload["sources"] = sources
    write_json(ROOT / "data" / "sources.json", payload)
    versions = read_json(ROOT / "data" / "source_versions.json", {"schema_version": "1.0", "events": []})
    versions["schema_version"] = "1.0"
    versions["generated_at"] = now_iso()
    write_json(ROOT / "data" / "source_versions.json", versions)
    print(f"Enriched {len(sources)} source records with heuristic metadata and initial content hashes.")

if __name__ == "__main__":
    main()
