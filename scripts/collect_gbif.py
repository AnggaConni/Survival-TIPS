from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from .common import ROOT, TIMEOUT, get_session, now_iso, read_json, stable_id, write_json

GBIF_API = "https://api.gbif.org/v1"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def license_allowed(value: str | None) -> bool:
    """Allow explicit CC0/PD, CC BY and CC BY-SA only; reject ambiguous and restrictive licenses."""
    license_value = (value or "").strip().lower()
    if not license_value:
        return False
    if any(marker in license_value for marker in ("by-nc", "by-nd", "all rights reserved", "unknown", "proprietary")):
        return False
    if license_value in {"cc0", "public domain", "pd"}:
        return True
    if "creativecommons.org/publicdomain/zero" in license_value:
        return True
    if "creativecommons.org/licenses/" in license_value:
        return ("/by/" in license_value or "/by-sa/" in license_value) and not any(
            marker in license_value for marker in ("by-nc", "by-nd")
        )
    return False


def search_occurrences(scientific_name: str, limit: int = 5) -> list[dict]:
    session = get_session()
    params = {"scientificName": scientific_name, "mediaType": "StillImage", "limit": min(max(limit * 10, 10), 100)}
    response = session.get(f"{GBIF_API}/occurrence/search", params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json().get("results", [])


def select_image(record: dict) -> tuple[dict, str] | tuple[None, None]:
    for media in record.get("media", []) or []:
        # Require media-level license; the occurrence-level license is not assumed to apply to a photo.
        license_value = media.get("license")
        url = media.get("identifier")
        if url and url.startswith("https://") and license_allowed(license_value):
            return media, license_value
    return None, None


def image_extension(url: str, mime: str = "") -> str:
    path = urlparse(url).path.lower()
    for extension in (".jpg", ".jpeg", ".png", ".webp"):
        if path.endswith(extension):
            return ".jpg" if extension == ".jpeg" else extension
    return ".png" if "png" in mime.lower() else ".jpg"


def download_image(url: str, target: Path) -> tuple[bool, str]:
    session = get_session()
    try:
        with session.get(url, timeout=TIMEOUT, stream=True) as response:
            response.raise_for_status()
            mime = response.headers.get("Content-Type", "").split(";")[0].lower()
            if not mime.startswith("image/"):
                return False, "not an image content type"
            data = bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data) > MAX_IMAGE_BYTES:
                    return False, "image exceeded size cap"
            if not data:
                return False, "empty image"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return True, mime
    except (requests.RequestException, OSError) as exc:
        return False, str(exc)


def collect_species(query: str, limit: int = 3) -> list[dict]:
    species_records = []
    for occurrence in search_occurrences(query, limit):
        media, license_value = select_image(occurrence)
        if not media:
            continue

        occurrence_key = occurrence.get("key")
        scientific_name = occurrence.get("scientificName") or query
        media_url = media["identifier"]
        record_id = stable_id(f"{occurrence_key}|{media_url}", "gbif")
        extension = image_extension(media_url, media.get("format", ""))
        relative_path = Path("assets") / "species" / f"{record_id}{extension}"
        target = ROOT / relative_path

        if not target.exists():
            ok, detail = download_image(media_url, target)
            if not ok:
                print(f"[gbif] Image skipped: {media_url} ({detail})")
                continue
        else:
            detail = "already downloaded"

        species_records.append({
            "id": record_id,
            "scientific_name": scientific_name,
            "common_name": occurrence.get("vernacularName"),
            "gbif_occurrence_key": occurrence_key,
            "gbif_taxon_key": occurrence.get("taxonKey"),
            "country": occurrence.get("country"),
            "locality": occurrence.get("locality"),
            "image_path": relative_path.as_posix(),
            "image_source_url": media_url,
            "image_license": license_value,
            "image_creator": media.get("creator"),
            "image_publisher": media.get("publisher"),
            "image_rights_holder": media.get("rightsHolder"),
            "gbif_record_url": f"https://www.gbif.org/occurrence/{occurrence_key}" if occurrence_key else None,
            "survival_use_evidence": "Not established by GBIF occurrence/photo data. Do not infer edibility, medicinal value, or safety.",
            "verification": {"status": "needs_review"},
            "retrieved_at": now_iso(),
        })
        print(f"[gbif] Saved {scientific_name}; license={license_value}")
        if len(species_records) >= limit:
            break
        time.sleep(0.2)
    return species_records


def run(queries: list[str], limit: int) -> None:
    path = ROOT / "data" / "species.json"
    payload = read_json(path, {"schema_version": "1.0", "species": []})
    merged = {item.get("id"): item for item in payload.get("species", []) if item.get("id")}
    added = 0
    for query in queries:
        for item in collect_species(query, limit):
            if item["id"] not in merged:
                added += 1
            merged[item["id"]] = item
    write_json(path, {"schema_version": "1.0", "generated_at": now_iso(), "species": list(merged.values())[-2000:]})
    print(f"[gbif] Added/updated {added}; total records: {len(merged)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect GBIF occurrence metadata and redistributable images.")
    parser.add_argument("--query", help="Scientific name or taxon search text. If omitted, use config/sources.json.")
    parser.add_argument("--limit", type=int, default=int(os.getenv("MAX_GBIF_IMAGES_PER_RUN", "3")))
    args = parser.parse_args()
    config = read_json(ROOT / "config" / "sources.json", {})
    queries = [args.query] if args.query else config.get("gbif_taxa", [])
    run(queries, max(1, args.limit))


if __name__ == "__main__":
    main()
