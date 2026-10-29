from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from .common import (
    ROOT, TIMEOUT, clean_text, get_session, is_http_url, now_iso,
    read_json, robots_allowed, safe_domain, stable_id, write_json,
)

CONFIG = read_json(ROOT / "config" / "sources.json", {})
TRUSTED_DOMAINS = set(CONFIG.get("trusted_domains", []))


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Use Tavily when configured, otherwise best-effort DuckDuckGo. Search is discovery, not validation."""
    api_key = os.getenv("TAVILY_API_KEY")
    if api_key:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            return [
                {"url": x.get("url", ""), "title": x.get("title", ""),
                 "snippet": x.get("content", ""), "search_provider": "tavily"}
                for x in data.get("results", [])
            ]
        except (requests.RequestException, ValueError) as exc:
            print(f"[search] Tavily failed: {exc}")

    try:
        from ddgs import DDGS
        with DDGS() as search:
            rows = list(search.text(query, max_results=max_results))
        return [
            {"url": row.get("href", ""), "title": row.get("title", ""),
             "snippet": row.get("body", ""), "search_provider": "duckduckgo"}
            for row in rows
        ]
    except Exception as exc:
        print(f"[search] DuckDuckGo unavailable: {exc}")
        return []


def collect_candidates(per_query: int = 4) -> list[dict]:
    session = get_session()
    candidates: dict[str, dict] = {}

    for query in CONFIG.get("queries", []):
        for item in search_web(query, per_query):
            url = item.get("url", "").strip()
            if is_http_url(url):
                candidates.setdefault(url, {**item, "source_type": "search", "query": query})

    for feed in CONFIG.get("rss_feeds", []):
        try:
            parsed = feedparser.parse(feed["url"])
            if getattr(parsed, "bozo", False):
                print(f"[rss] Feed parse warning: {feed['url']}")
            for entry in parsed.entries[:15]:
                url = entry.get("link", "").strip()
                if not is_http_url(url):
                    continue
                candidates.setdefault(url, {
                    "url": url,
                    "title": entry.get("title", ""),
                    "snippet": BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True),
                    "source_type": "rss",
                    "feed_name": feed.get("name", ""),
                    "search_provider": None,
                })
        except Exception as exc:
            print(f"[rss] Failed {feed.get('url')}: {exc}")

    def rank(item: dict) -> tuple[int, str]:
        domain = safe_domain(item["url"])
        is_trusted = any(domain == d or domain.endswith("." + d) for d in TRUSTED_DOMAINS)
        return (0 if is_trusted else 1, item["url"])

    return sorted(candidates.values(), key=rank)


def extract_page(candidate: dict) -> dict | None:
    url = candidate["url"]
    session = get_session()
    if not robots_allowed(url, session):
        print(f"[skip] robots policy disallows or could not be checked: {url}")
        return None

    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type:
            return None

        max_bytes = 3_000_000
        chunks, total = [], 0
        for chunk in response.iter_content(chunk_size=65536):
            total += len(chunk)
            if total > max_bytes:
                print(f"[skip] page exceeds {max_bytes} bytes: {url}")
                return None
            chunks.append(chunk)
        html = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
            tag.decompose()

        title = soup.title.get_text(" ", strip=True) if soup.title else candidate.get("title", "")
        main = soup.find("main") or soup.find("article") or soup.body or soup
        text = clean_text(main.get_text(" ", strip=True))
        if len(text) < 250:
            return None

        final_url = response.url
        return {
            "id": stable_id(final_url, "src"),
            "url": final_url,
            "title": (title or candidate.get("title") or "Untitled")[:300],
            "domain": safe_domain(final_url),
            "text": text,
            "snippet": clean_text(candidate.get("snippet", ""), 1200),
            "source_type": candidate.get("source_type", "search"),
            "feed_name": candidate.get("feed_name"),
            "search_provider": candidate.get("search_provider"),
            "retrieved_at": now_iso(),
        }
    except (requests.RequestException, UnicodeError) as exc:
        print(f"[fetch] Failed {url}: {exc}")
        return None
    finally:
        time.sleep(0.25)


def collect_sources(limit: int = 8) -> list[dict]:
    candidates = collect_candidates()
    existing_payload = read_json(ROOT / "data" / "sources.json", {"schema_version": "1.0", "sources": []})
    existing = {row.get("url"): row for row in existing_payload.get("sources", []) if row.get("url")}
    fetched = 0

    for candidate in candidates:
        if fetched >= max(1, limit):
            break
        url = candidate["url"]
        # Keep stable source records across workflow runs; skip URLs already ingested.
        if url in existing and existing[url].get("text"):
            continue
        page = extract_page(candidate)
        if not page:
            continue
        existing[page["url"]] = page
        fetched += 1
        print(f"[source] {page['title']} — {page['url']}")

    payload = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "sources": list(existing.values())[-2000:],
    }
    write_json(ROOT / "data" / "sources.json", payload)
    print(f"[source] Added {fetched}; total stored: {len(payload['sources'])}")
    return [row for row in payload["sources"] if row.get("retrieved_at") == payload["generated_at"]]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=int(os.getenv("MAX_ARTICLES_PER_RUN", "8")))
    args = parser.parse_args()
    collect_sources(args.limit)
