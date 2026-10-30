from __future__ import annotations
import os, time, feedparser, requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from .common import ROOT, TIMEOUT, clean_text, get_session, is_http_url, now_iso, read_json, robots_allowed, safe_domain, stable_id, write_json
from .source_quality import annotate_source, content_hash
CONFIG=read_json(ROOT/"config"/"sources.json",{})
TRUSTED_DOMAINS=set(CONFIG.get("trusted_domains",[]))
def search_web(query,max_results=5):
    """Use Tavily if configured, otherwise DuckDuckGo. Search results are discovery leads only."""
    key=os.getenv("TAVILY_API_KEY")
    if key:
        try:
            r=requests.post("https://api.tavily.com/search",json={"api_key":key,"query":query,"max_results":max_results,"search_depth":"basic"},timeout=TIMEOUT)
            r.raise_for_status()
            return [{"url":x.get("url",""),"title":x.get("title",""),"snippet":x.get("content",""),"search_provider":"tavily"} for x in r.json().get("results",[])]
        except (requests.RequestException,ValueError) as exc: print(f"[search] Tavily failed: {exc}")
    try:
        from ddgs import DDGS
        with DDGS() as search: rows=list(search.text(query,max_results=max_results))
        return [{"url":x.get("href",""),"title":x.get("title",""),"snippet":x.get("body",""),"search_provider":"duckduckgo"} for x in rows]
    except Exception as exc:
        print(f"[search] DuckDuckGo unavailable: {exc}"); return []
def filter_candidates(items):
    """Keep only trusted, topic-relevant sources; search rank alone is not a quality gate."""
    practical_title_terms = (
        "guide", "manual", "handbook", "how to", "toolbox", "treatment",
        "shelter", "standard", "field guide", "factsheet", "procedure",
        "cultivation", "food safety", "water storage", "handwashing", "repair",
        "construction", "irrigation", "compost", "seed saving", "preservation",
        "maintenance", "design specification", "checklist", "preparedness",
        "evacuation", "emergency", "sanitation", "hygiene",
    )
    topic_terms = (
        "emergency", "disaster", "water", "wash", "shelter", "food", "nutrition",
        "agriculture", "garden", "crop", "seed", "soil", "irrigation", "preservation",
        "sanitation", "hygiene", "first aid", "construction", "material", "energy",
        "repair", "treatment", "preparedness", "evacuation", "compost", "livestock",
        "fire", "safety", "biodiversity", "species", "ecology", "forest", "coastal",
        "flood", "drought",
    )
    news_title_terms = (
        "news", "statement", "signing ceremony", "contribution agreement",
        "funding", "pledge", "donation", "appoint", "visit", "meeting",
        "press release", "partnership", "launches", "announces", "cast",
    )
    accepted = []
    for item in items:
        domain = safe_domain(item.get("url", ""))
        trusted = any(domain == d or domain.endswith("." + d) for d in TRUSTED_DOMAINS)
        title = str(item.get("title", "")).casefold()
        practical = any(term in title for term in practical_title_terms)
        relevant = practical or any(term in title for term in topic_terms)
        news_only = any(term in title for term in news_title_terms) and not practical
        if trusted and relevant and not news_only:
            accepted.append(item)

    def rank(item):
        title = str(item.get("title", "")).casefold()
        practical = any(term in title for term in practical_title_terms)
        return (0 if practical else 1, item.get("url", ""))

    return sorted(accepted, key=rank)


def collect_candidates(per_query=4):
    candidates={}
    for query in CONFIG.get("queries",[]):
        for item in search_web(query,per_query):
            url=item.get("url","").strip()
            if is_http_url(url): candidates.setdefault(url,{**item,"source_type":"search","query":query})
    for feed in CONFIG.get("rss_feeds",[]):
        try:
            parsed=feedparser.parse(feed["url"])
            for entry in parsed.entries[:15]:
                url=entry.get("link","").strip()
                if is_http_url(url):
                    candidates.setdefault(url,{"url":url,"title":entry.get("title",""),"snippet":BeautifulSoup(entry.get("summary",""),"html.parser").get_text(" ",strip=True),"source_type":"rss","feed_name":feed.get("name",""),"search_provider":None})
        except Exception as exc: print(f"[rss] Failed {feed.get('url')}: {exc}")
    return filter_candidates(candidates.values())
def extract_page(candidate):
    session=get_session()
    if not robots_allowed(candidate["url"],session):
        print(f"[skip] robots disallows or unavailable: {candidate['url']}"); return None
    try:
        with session.get(candidate["url"],timeout=TIMEOUT,allow_redirects=True,stream=True) as r:
            r.raise_for_status()
            if "text/html" not in r.headers.get("Content-Type","").lower(): return None
            chunks=[]; size=0
            for chunk in r.iter_content(65536):
                size+=len(chunk)
                if size>3_000_000: print("[skip] page exceeds size limit"); return None
                chunks.append(chunk)
            soup=BeautifulSoup(b"".join(chunks).decode(r.encoding or "utf-8",errors="replace"),"html.parser")
            for tag in soup(["script","style","nav","footer","header","aside","form","noscript"]): tag.decompose()
            title=soup.title.get_text(" ",strip=True) if soup.title else candidate.get("title","")
            main=soup.find("main") or soup.find("article") or soup.body or soup
            text=clean_text(main.get_text(" ",strip=True))
            if len(text)<250: return None
            url=r.url
            return {"id":stable_id(url,"src"),"url":url,"title":(title or candidate.get("title") or "Untitled")[:300],"domain":safe_domain(url),"text":text,"snippet":clean_text(candidate.get("snippet",""),1200),"source_type":candidate.get("source_type","search"),"feed_name":candidate.get("feed_name"),"search_provider":candidate.get("search_provider"),"retrieved_at":now_iso()}
    except (requests.RequestException,UnicodeError) as exc:
        print(f"[fetch] Failed {candidate['url']}: {exc}"); return None
    finally: time.sleep(.25)
def collect_sources(limit=8):
    candidates=collect_candidates()
    old=read_json(ROOT/"data"/"sources.json",{"schema_version":"1.0","sources":[]})
    merged={x.get("url"):annotate_source(x) for x in old.get("sources",[]) if x.get("url")}
    versions=read_json(ROOT/"data"/"source_versions.json",{"schema_version":"1.0","events":[]})
    added=0; refreshed=0
    refresh_days=max(1,int(os.getenv("SOURCE_REFRESH_DAYS","30")))
    now=datetime.now(timezone.utc)
    for candidate in candidates:
        if added+refreshed>=max(1,limit): break
        existing=merged.get(candidate["url"])
        if existing and existing.get("text"):
            checked=existing.get("last_checked_at") or existing.get("retrieved_at")
            try:
                checked_at=datetime.fromisoformat(str(checked).replace("Z","+00:00"))
                if checked_at.tzinfo is None: checked_at=checked_at.replace(tzinfo=timezone.utc)
            except (TypeError,ValueError):
                checked_at=now-timedelta(days=refresh_days+1)
            if now-checked_at < timedelta(days=refresh_days): continue
        page=extract_page(candidate)
        if not page: continue
        page=annotate_source(page)
        if existing:
            old_hash=existing.get("content_hash") or content_hash(existing.get("text",""))
            new_hash=content_hash(page.get("text",""))
            page["first_seen_at"]=existing.get("first_seen_at") or existing.get("retrieved_at")
            page["last_checked_at"]=page.get("retrieved_at")
            if old_hash == new_hash:
                page["quality_assessment"]=existing.get("quality_assessment") or page.get("quality_assessment")
                page["version"]=existing.get("version",1)
                page["content_changed_at"]=existing.get("content_changed_at") or existing.get("retrieved_at")
            else:
                page["version"]=int(existing.get("version",1))+1
                page["previous_content_hash"]=old_hash
                page["content_changed_at"]=page.get("retrieved_at")
                versions.setdefault("events",[]).append({"source_url":page["url"],"version":page["version"],"previous_content_hash":old_hash,"content_hash":new_hash,"changed_at":page.get("retrieved_at"),"event":"source_content_changed"})
                print(f"[source] Content changed: {page['url']} (v{page['version']})")
            merged[page["url"]]=page; refreshed+=1
        else:
            page["version"]=1
            merged[page["url"]]=page; added+=1
        print(f"[source] Stored {page['title']} — {page['url']}")
    payload={"schema_version":"1.1","generated_at":now_iso(),"sources":list(merged.values())[-2000:]}
    versions["generated_at"]=now_iso()
    versions["events"]=versions.get("events",[])[-5000:]
    write_json(ROOT/"data"/"sources.json",payload)
    write_json(ROOT/"data"/"source_versions.json",versions)
    print(f"[source] Added {added}; refreshed {refreshed}; total {len(payload['sources'])}")
    return payload["sources"]
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--limit",type=int,default=int(os.getenv("MAX_ARTICLES_PER_RUN","8")))
    collect_sources(p.parse_args().limit)
