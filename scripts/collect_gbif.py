from __future__ import annotations
import argparse, os, time
from pathlib import Path
from urllib.parse import urlparse
import requests
from .common import ROOT, TIMEOUT, get_session, now_iso, read_json, stable_id, write_json
GBIF_API="https://api.gbif.org/v1"; MAX_IMAGE_BYTES=8*1024*1024
def license_allowed(value):
    value=(value or "").strip().lower()
    if not value or any(x in value for x in ("by-nc","by-nd","all rights reserved","unknown","proprietary")): return False
    if value in {"cc0","public domain","pd"}: return True
    if "creativecommons.org/publicdomain/zero" in value: return True
    if "creativecommons.org/licenses/" in value: return ("/by/" in value or "/by-sa/" in value) and not any(x in value for x in ("by-nc","by-nd"))
    return False
def search_occurrences(name,limit=3):
    r=get_session().get(f"{GBIF_API}/occurrence/search",params={"scientificName":name,"mediaType":"StillImage","limit":min(max(limit*10,10),100)},timeout=TIMEOUT)
    r.raise_for_status(); return r.json().get("results",[])
def select_image(record):
    for media in record.get("media",[]) or []:
        lic=media.get("license")
        url=media.get("identifier")
        if url and url.startswith("https://") and license_allowed(lic): return media,lic
    return None,None
def extension(url,mime=""):
    path=urlparse(url).path.lower()
    for ext in (".jpg",".jpeg",".png",".webp"):
        if path.endswith(ext): return ".jpg" if ext==".jpeg" else ext
    return ".png" if "png" in mime.lower() else ".jpg"
def download_image(url,target):
    try:
        with get_session().get(url,timeout=TIMEOUT,stream=True) as r:
            r.raise_for_status(); mime=r.headers.get("Content-Type","").split(";")[0].lower()
            if not mime.startswith("image/"): return False,"not an image content type"
            body=bytearray()
            for chunk in r.iter_content(65536):
                body.extend(chunk)
                if len(body)>MAX_IMAGE_BYTES: return False,"image exceeds 8MB"
            if not body: return False,"empty image"
            target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(body)
        return True,mime
    except (requests.RequestException,OSError) as exc: return False,str(exc)
def collect_species(query,limit=3):
    out=[]
    for row in search_occurrences(query,limit):
        media,lic=select_image(row)
        if not media: continue
        key=row.get("key"); sci=row.get("scientificName") or query; url=media["identifier"]
        rid=stable_id(f"{key}|{url}","gbif"); rel=Path("assets")/"species"/f"{rid}{extension(url,media.get('format',''))}"; path=ROOT/rel
        if not path.exists():
            ok,why=download_image(url,path)
            if not ok: print(f"[gbif] skipped {url}: {why}"); continue
        out.append({"id":rid,"scientific_name":sci,"common_name":row.get("vernacularName"),"gbif_occurrence_key":key,"gbif_taxon_key":row.get("taxonKey"),"country":row.get("country"),"locality":row.get("locality"),"image_path":rel.as_posix(),"image_source_url":url,"image_license":lic,"image_creator":media.get("creator"),"image_publisher":media.get("publisher"),"image_rights_holder":media.get("rightsHolder"),"gbif_record_url":f"https://www.gbif.org/occurrence/{key}" if key else None,"survival_use_evidence":"Not established by GBIF occurrence/photo data. Never infer edibility or safety.","verification":{"status":"needs_review"},"retrieved_at":now_iso()})
        print(f"[gbif] {sci} | {lic}")
        if len(out)>=limit: break
        time.sleep(.2)
    return out
def run(queries,limit=3):
    path=ROOT/"data"/"species.json"; data=read_json(path,{"schema_version":"1.0","species":[]}); merged={x.get("id"):x for x in data.get("species",[]) if x.get("id")}; count=0
    for query in queries:
        for row in collect_species(query,limit):
            if row["id"] not in merged: count+=1
            merged[row["id"]]=row
    write_json(path,{"schema_version":"1.0","generated_at":now_iso(),"species":list(merged.values())[-2000:]})
    print(f"[gbif] New/updated {count}; total {len(merged)}")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--query"); p.add_argument("--limit",type=int,default=int(os.getenv("MAX_GBIF_IMAGES_PER_RUN","3")))
    a=p.parse_args(); c=read_json(ROOT/"config"/"sources.json",{}); run([a.query] if a.query else c.get("gbif_taxa",[]),max(1,a.limit))
if __name__=="__main__": main()
