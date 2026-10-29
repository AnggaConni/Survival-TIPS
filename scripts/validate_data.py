from __future__ import annotations
from .common import ROOT, read_json
def validate():
    errors=[]; data={name:read_json(ROOT/"data"/f"{name}.json",{}) for name in ("sources","tips","species")}
    for name,payload in data.items():
        if not isinstance(payload.get(name),list): errors.append(f"data/{name}.json must have '{name}' array")
    ids=set()
    for tip in data["tips"].get("tips",[]):
        for field in ("id","title","category","summary","sources","verification"):
            if field not in tip: errors.append(f"tip missing {field}: {tip.get('id')}")
        if tip.get("id") in ids: errors.append(f"duplicate tip ID: {tip.get('id')}")
        ids.add(tip.get("id"))
        if not tip.get("sources"): errors.append(f"tip missing sources: {tip.get('id')}")
    for row in data["species"].get("species",[]):
        for field in ("image_path","image_license","image_source_url"):
            if not row.get(field): errors.append(f"species missing {field}: {row.get('id')}")
    if errors: print("\n".join(errors)); return False
    print(f"Data OK: {len(data['sources']['sources'])} sources, {len(data['tips']['tips'])} tips, {len(data['species']['species'])} species/images.")
    return True
if __name__=="__main__": raise SystemExit(0 if validate() else 1)
