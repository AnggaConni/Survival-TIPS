from __future__ import annotations

import argparse
import os

from .collect_gbif import run as run_gbif
from .collect_sources import collect_sources
from .common import ROOT, now_iso, read_json, write_json
from .extract_tips import process_saved_sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect source-linked survival knowledge candidates.")
    parser.add_argument("--limit", type=int, default=int(os.getenv("MAX_ARTICLES_PER_RUN", "8")))
    parser.add_argument("--gbif-limit", type=int, default=int(os.getenv("MAX_GBIF_IMAGES_PER_RUN", "3")))
    parser.add_argument("--search-only", action="store_true", help="Collect source pages only; do not call AI or GBIF.")
    args = parser.parse_args()

    print("=== Survival-TIPS collector ===")
    collect_sources(limit=max(1, args.limit))

    if not args.search_only:
        process_saved_sources()
        config = read_json(ROOT / "config" / "sources.json", {})
        run_gbif(config.get("gbif_taxa", []), max(1, args.gbif_limit))

    print(f"Finished at {now_iso()}")


if __name__ == "__main__":
    main()
