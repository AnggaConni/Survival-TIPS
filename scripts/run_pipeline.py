from __future__ import annotations
import argparse, os
from .collect_gbif import run as run_gbif
from .collect_sources import collect_sources
from .common import ROOT, now_iso, read_json
from .extract_tips import process_saved_sources
def main():
    p=argparse.ArgumentParser(description="Collect source-linked survival knowledge candidates.")
    p.add_argument("--limit",type=int,default=int(os.getenv("MAX_ARTICLES_PER_RUN","8")))
    p.add_argument("--gbif-limit",type=int,default=int(os.getenv("MAX_GBIF_IMAGES_PER_RUN","3")))
    p.add_argument("--ai-limit",type=int,default=5)
    p.add_argument("--search-only",action="store_true")
    a=p.parse_args(); print("=== Survival-TIPS data collector ===")
    collect_sources(max(1,a.limit))
    if not a.search_only:
        process_saved_sources(max_sources=max(1,a.ai_limit))
        c=read_json(ROOT/"config"/"sources.json",{})
        run_gbif(c.get("gbif_taxa",[]),max(1,a.gbif_limit))
    print(f"Finished at {now_iso()}")
if __name__=="__main__": main()
