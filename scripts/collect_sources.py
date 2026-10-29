from __future__ import annotations
import os, time, feedparser, requests
from bs4 import BeautifulSoup
from .common import ROOT, TIMEOUT, clean_text, get_session, is_http_url, now_iso, read_json, robots_allowed, safe_domain, stable_id, write_json
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
    practical_title_terms = (
        "guide", "manual", "handbook", "how to", "toolbox", "treatment",
        "shelter solutions", "standards", "technical", "field guide",
        "factsheet", "procedure", "cultivation", "food safety", "water storage",
        "handwashing", "repair", "construction", "irrigation", "compost",
        "seed saving", "preservation", "maintenance", "design specification",
    )
    news_title_terms = (
        "news", "statement", "signing ceremony", "contribution agreement",
        "funding", "pledge", "donation", "appoint", "visit", "meeting",
        "press release", "partnership", "launches", "announces",
    )
    def rank(item):
        domain=safe_domain(item["url"])
        trusted=any(domain==d or domain.endswith("."+d) for d in TRUSTED_DOMAINS)
        title=str(item.get("title", "")).casefold()
        query=str(item.get("query", "")).casefold()
        practical=any(term in title for term in practical_title_terms) or any(term in query for term in practical_title_terms)
        likely_news=any(term in title for term in news_title_terms)
        # Put practical manuals/guides first; de-prioritize announcement-style RSS/news.
        return (1 if likely_news and not practical else 0, 0 if practical else 1, 0 if trusted else 1, item["url"])
    return sorted(candidates.values(),key=rank)
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
    candidates=collect_candidates(); old=read_json(ROOT/"data"/"sources.json",{"schema_version":"1.0","sources":[]})
    merged={x.get("url"):x for x in old.get("sources",[]) if x.get("url")}; added=0
    for candidate in candidates:
        if added>=max(1,limit): break
        if candidate["url"] in merged and merged[candidate["url"]].get("text"): continue
        page=extract_page(candidate)
        if page:
            merged[page["url"]]=page; added+=1; print(f"[source] {page['title']} — {page['url']}")
    payload={"schema_version":"1.0","generated_at":now_iso(),"sources":list(merged.values())[-2000:]}
    write_json(ROOT/"data"/"sources.json",payload)
    print(f"[source] Added {added}; total {len(payload['sources'])}")
    return payload["sources"]
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--limit",type=int,default=int(os.getenv("MAX_ARTICLES_PER_RUN","8")))
    collect_sources(p.parse_args().limit)
