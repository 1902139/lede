#!/usr/bin/env python3
"""
Lede news fetcher.

Pulls RSS feeds for every outlet in data/ownership.json, clusters articles
that cover the same story, and writes data/stories.json for the static site.

Usage:
    python fetch_news.py                 # fetch live feeds
    python fetch_news.py --fixtures DIR  # parse local files instead (testing)

Requires: pip install feedparser
"""
import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser

HERE = Path(__file__).resolve().parent

def _find_ownership():
    """Locate ownership.json wherever it lives (root, data/, or one level up)."""
    for cand in (HERE / "ownership.json",
                 HERE / "data" / "ownership.json",
                 HERE.parent / "ownership.json",
                 HERE.parent / "data" / "ownership.json"):
        if cand.exists():
            return cand
    searched = "\n  ".join(str(c) for c in (
        HERE / "ownership.json", HERE / "data" / "ownership.json",
        HERE.parent / "ownership.json", HERE.parent / "data" / "ownership.json"))
    print("ERROR: could not find ownership.json. Looked in:\n  " + searched, file=sys.stderr)
    print("Files next to this script: " + ", ".join(sorted(x.name for x in HERE.iterdir())), file=sys.stderr)
    sys.exit(1)

OWNERSHIP = _find_ownership()
ROOT = OWNERSHIP.parent
OUT = ROOT / "stories.json"

WINDOW_HOURS = 72          # only cluster articles this recent
MAX_STORIES = 40           # stories shown on the site
JACCARD_JOIN = 0.20        # title-token similarity to join a cluster
SHARED_JOIN = 3            # or at least this many shared significant tokens
UNDERREPORTED_CORP_SHARE = 0.34  # corp+family share at or below this => underreported
USER_AGENT = "LedeAggregator/0.1 (+https://github.com/your-user/lede)"

STOPWORDS = set("""
a an the and or but of in on at to for with from by as is are was were be been
it its this that these those he she they we you i his her their our your not
no yes new says said say after before over under about into out up down amid
more most than then will would could should can may might have has had do does
did what when where who whom why how which while during against between
""".split())

OPINION_HINTS = re.compile(r"opinion|editorial|commentary|comment-is-free|commentisfree|op-ed|column", re.I)


def tokens(text):
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def entry_time(e):
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(e, attr, None) or (e.get(attr) if isinstance(e, dict) else None)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return datetime.now(timezone.utc)


def detect_kind(entry, feed_kind):
    if feed_kind == "opinion":
        return "opinion"
    link = entry.get("link", "") or ""
    cats = " ".join(t.get("term", "") for t in entry.get("tags", []) if isinstance(t, dict))
    if OPINION_HINTS.search(link) or OPINION_HINTS.search(cats):
        return "opinion"
    return "news"


def fetch_all(outlets, fixtures=None):
    """Return list of article dicts from every reachable feed."""
    articles, feed_report = [], []
    now = datetime.now(timezone.utc)
    for key, o in outlets.items():
        for fi, feed in enumerate(o.get("feeds", [])):
            src = feed["url"]
            if fixtures:
                if fi > 0:
                    continue  # fixture mode: one parse per outlet
                # fixture mode: look for a local file named <outletkey>[-n].xml
                candidates = sorted(Path(fixtures).glob(f"{key}*.xml"))
                if not candidates:
                    continue
                parsed_list = [feedparser.parse(str(p)) for p in candidates]
            else:
                try:
                    parsed_list = [feedparser.parse(src, agent=USER_AGENT)]
                except Exception as ex:
                    feed_report.append({"feed": src, "ok": False, "error": str(ex)})
                    continue
            for parsed in parsed_list:
                ok = not parsed.get("bozo") or bool(parsed.get("entries"))
                feed_report.append({"feed": src, "ok": ok, "entries": len(parsed.get("entries", []))})
                for e in parsed.get("entries", [])[:40]:
                    title = (e.get("title") or "").strip()
                    link = (e.get("link") or "").strip()
                    if not title or not link:
                        continue
                    when = entry_time(e)
                    if (now - when).total_seconds() > WINDOW_HOURS * 3600:
                        continue
                    summary = re.sub(r"<[^>]+>", " ", e.get("summary", "") or "")
                    summary = re.sub(r"\s+", " ", summary).strip()[:500]
                    articles.append({
                        "outlet": key,
                        "title": title,
                        "url": link,
                        "author": (e.get("author") or "").strip() or None,
                        "kind": detect_kind(e, feed["kind"]),
                        "published": when.isoformat(),
                        "summary": summary or None,
                        "_tokens": tokens(title),
                    })
    return articles, feed_report


def cluster(articles):
    """Greedy clustering on title-token overlap."""
    clusters = []
    for a in sorted(articles, key=lambda x: x["published"], reverse=True):
        best, best_score = None, 0.0
        for c in clusters:
            shared = a["_tokens"] & c["tokens"]
            union = a["_tokens"] | c["tokens"]
            j = len(shared) / len(union) if union else 0.0
            if (j >= JACCARD_JOIN or len(shared) >= SHARED_JOIN) and j > best_score:
                best, best_score = c, j
        if best:
            # skip near-duplicate from the same outlet
            if any(x["outlet"] == a["outlet"] and len(x["_tokens"] & a["_tokens"]) >= SHARED_JOIN
                   for x in best["articles"]):
                continue
            best["articles"].append(a)
            best["tokens"] |= a["_tokens"]
        else:
            clusters.append({"articles": [a], "tokens": set(a["_tokens"])})
    return clusters


def shape(clusters, outlets):
    stories = []
    for c in clusters:
        arts = sorted(c["articles"], key=lambda x: x["published"], reverse=True)
        counts = {}
        for a in arts:
            t = outlets[a["outlet"]]["type"]
            counts[t] = counts.get(t, 0) + 1
        total = len(arts)
        corp_share = (counts.get("corp", 0) + counts.get("family", 0)) / total
        # headline: prefer a nonprofit/public/wire-style source, else newest
        lead = next((a for a in arts if outlets[a["outlet"]]["type"] in ("nonprofit", "pub")), arts[0])
        sid = hashlib.md5((lead["title"] + lead["url"]).encode()).hexdigest()[:10]
        stories.append({
            "id": sid,
            "headline": lead["title"],
            "updated": arts[0]["published"],
            "outletCount": len({a["outlet"] for a in arts}),
            "counts": counts,
            "newsCount": sum(1 for a in arts if a["kind"] == "news"),
            "opinionCount": sum(1 for a in arts if a["kind"] == "opinion"),
            "underreported": total >= 2 and corp_share <= UNDERREPORTED_CORP_SHARE,
            "articles": [{k: v for k, v in a.items() if k != "_tokens"} for a in arts],
        })
    # multi-outlet stories first, then by recency
    stories.sort(key=lambda s: (-s["outletCount"], s["updated"]), reverse=False)
    stories.sort(key=lambda s: s["updated"], reverse=True)
    stories.sort(key=lambda s: -s["outletCount"])
    return stories[:MAX_STORIES]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", help="directory of local RSS files for testing")
    args = ap.parse_args()

    own = json.loads(OWNERSHIP.read_text())
    outlets = own["outlets"]

    articles, report = fetch_all(outlets, fixtures=args.fixtures)
    ok_feeds = sum(1 for r in report if r.get("ok"))
    print(f"feeds ok: {ok_feeds}/{len(report)}, articles in window: {len(articles)}", file=sys.stderr)
    for r in report:
        if not r.get("ok"):
            print(f"  FAILED: {r['feed']} {r.get('error','')}", file=sys.stderr)

    stories = shape(cluster(articles), outlets)
    OUT.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(),
        "storyCount": len(stories),
        "feedsOk": ok_feeds,
        "feedsTotal": len(report),
        "stories": stories,
    }, indent=1))
    print(f"wrote {OUT} with {len(stories)} stories", file=sys.stderr)


if __name__ == "__main__":
    main()
