from __future__ import annotations

from .common import ROOT, read_json


def validate() -> bool:
    errors = []
    payloads = {
        "sources": read_json(ROOT / "data" / "sources.json", {}),
        "tips": read_json(ROOT / "data" / "tips.json", {}),
        "species": read_json(ROOT / "data" / "species.json", {}),
    }

    for name, payload in payloads.items():
        if not isinstance(payload.get(name), list):
            errors.append(f"data/{name}.json must have an array named '{name}'")

    seen_tip_ids = set()
    for tip in payloads["tips"].get("tips", []):
        for field in ("id", "title", "category", "summary", "sources", "verification"):
            if field not in tip:
                errors.append(f"tip missing '{field}': {tip.get('id')}")
        if tip.get("id") in seen_tip_ids:
            errors.append(f"duplicate tip id: {tip.get('id')}")
        seen_tip_ids.add(tip.get("id"))
        if not tip.get("sources"):
            errors.append(f"tip without source link: {tip.get('id')}")

    for row in payloads["species"].get("species", []):
        if not row.get("image_path") or not row.get("image_license") or not row.get("image_source_url"):
            errors.append(f"species image record missing path/license/source: {row.get('id')}")

    if errors:
        print("\n".join(errors))
        return False

    print(
        "Data OK — "
        f"{len(payloads['sources']['sources'])} sources, "
        f"{len(payloads['tips']['tips'])} tips, "
        f"{len(payloads['species']['species'])} species/image records."
    )
    return True


if __name__ == "__main__":
    raise SystemExit(0 if validate() else 1)
