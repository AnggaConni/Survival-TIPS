from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
USER_AGENT = os.getenv("USER_AGENT", "Survival-TIPS/0.1 (educational research)")
HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,application/json,application/rss+xml,*/*"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_id(value: str, prefix: str = "item") -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:14]}"


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"} and bool(urlparse(url).netloc)


def clean_text(text: str, max_chars: int = 18000) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:max_chars]


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def robots_allowed(url: str, session: requests.Session | None = None) -> bool:
    """Return False when robots policy cannot be checked (except an explicit 404)."""
    from urllib.parse import urlunparse

    session = session or get_session()
    parsed = urlparse(url)
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    try:
        response = session.get(robots_url, timeout=TIMEOUT)
        if response.status_code == 404:
            return True
        response.raise_for_status()
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(response.text.splitlines())
        return parser.can_fetch(USER_AGENT, url)
    except requests.RequestException:
        return False
