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

import socket

import feedparser

# A dead host used to hang the run for minutes; cap every network read.
socket.setdefaulttimeout(12)

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
FEED_OUT = ROOT / "feed.xml"
UNDER_OUT = ROOT / "underreported.xml"
HIST_OUT = ROOT / "history.json"

WINDOW_HOURS = 72          # only cluster articles this recent
MAX_STORIES = 60           # stories shown on the site
JACCARD_JOIN = 0.20        # title-token similarity to join a cluster
SHARED_JOIN = 3            # or at least this many shared significant tokens
UNDERREPORTED_CORP_SHARE = 0.34  # corp+family share at or below this => underreported
# Mozilla-prefixed so WAFs don't reject us, but self-identifying with a contact URL.
USER_AGENT = ("Mozilla/5.0 (compatible; LedeBot/1.0; +https://github.com/joelbarandi/lede) feedparser")
SITE_URL = "https://joelbarandi.github.io/lede/"
FEED_TIMEOUT = 12          # seconds per feed — stops dead hosts stalling the whole run

STOPWORDS = set("""
a an the and or but of in on at to for with from by as is are was were be been
it its this that these those he she they we you i his her their our your not
no yes new says said say after before over under about into out up down amid
more most than then will would could should can may might have has had do does
did what when where who whom why how which while during against between
""".split())

OPINION_HINTS = re.compile(r"opinion|editorial|commentary|comment-is-free|commentisfree|op-ed|column", re.I)


TOPICS = [
    ("Politics", """election elections senate congress house president trump biden vance
        campaign vote voter ballot governor democrat republican gop white lawmakers
        legislature primary impeach subpoena caucus"""),
    ("Justice & Policing", """court supreme judge lawsuit indicted indictment prosecutor
        police officer arrest sentencing prison jail ice deportation immigration lawsuit
        attorney trial verdict sued charges felony detained"""),
    ("World", """ukraine russia gaza israel china iran nato europe india africa mexico
        canada britain france germany japan korea war military strike embassy diplomatic
        border troops ceasefire"""),
    ("Business & Economy", """economy inflation jobs unemployment wage wages market stocks
        tariff trade fed reserve earnings layoffs merger acquisition ipo bank housing
        prices union strike labor billion revenue"""),
    ("Climate & Energy", """climate emissions heat wildfire hurricane flood drought storm
        energy solar wind oil gas coal grid power renewable epa pollution warming
        temperature"""),
    ("Tech", """ai artificial intelligence tech software app google apple meta amazon
        microsoft openai chip semiconductor data privacy hacked breach cyber crypto
        algorithm platform users startup"""),
    ("Health", """health hospital medical doctors patients disease virus vaccine cdc fda
        drug medicaid medicare insurance outbreak cancer mental care nurses"""),
    ("Culture & Sport", """film movie music album artist book game nfl nba mlb soccer
        olympics championship team player coach season concert festival award celebrity
        streaming"""),
]
TOPIC_WORDS = [(name, set(kw.split())) for name, kw in TOPICS]


def classify_topic(text):
    raw = re.findall(r"[a-z']+", (text or "").lower())
    # crude singularisation so "hospitals" matches "hospital"
    toks = set(raw) | {w[:-1] for w in raw if len(w) > 3 and w.endswith("s")}
    best, score = "Other", 0
    for name, words in TOPIC_WORDS:
        n = len(toks & words)
        if n > score:
            best, score = name, n
    return best


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
                    raw_sum = e.get("summary", "") or ""
                    for c in (e.get("content") or []):
                        if isinstance(c, dict) and len(c.get("value", "")) > len(raw_sum):
                            raw_sum = c["value"]
                    summary = re.sub(r"<[^>]+>", " ", raw_sum)
                    summary = re.sub(r"\s+", " ", summary).strip()[:1200]
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


EMPH_STOP = STOPWORDS | set("""
says said say new report reports amid after before over under first last two three
plans plan could would may might set gets get make makes take takes back down up
year years day days week month according calls call top new news live updates update
""".split())


def emphasis(arts, outlets):
    """Which words show up in one ownership group's headlines and not the other's.

    Pure word counting on headlines — not a judgement about intent. Only computed
    when both groups have at least two articles, since one headline is noise.
    """
    big, indie = [], []
    for a in arts:
        t = outlets[a["outlet"]]["type"]
        text = a["title"] + " " + (a.get("summary") or "")[:400]
        (big if t in ("corp", "family") else indie).append(text)
    if len(big) < 2 or len(indie) < 2:
        return None

    def terms(titles):
        c = {}
        for t in titles:
            for w in set(re.findall(r"[a-z][a-z'-]{3,}", t.lower())):
                if w not in EMPH_STOP:
                    c[w] = c.get(w, 0) + 1
        return c

    cb, ci = terms(big), terms(indie)
    only_big = sorted([w for w, n in cb.items() if n >= 2 and w not in ci],
                      key=lambda w: -cb[w])[:6]
    only_indie = sorted([w for w, n in ci.items() if n >= 2 and w not in cb],
                        key=lambda w: -ci[w])[:6]
    if not only_big and not only_indie:
        return None
    return {"bigCount": len(big), "indieCount": len(indie),
            "big": only_big, "indie": only_indie}


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
        topic_src = " ".join(a["title"] for a in arts)
        cands = [a for a in arts if a.get("summary") and len(a["summary"]) > 60]
        src = max(cands, key=lambda a: len(a["summary"])) if cands else None
        summary = src["summary"] if src else None
        summary_from = src["outlet"] if src else None
        if summary and len(summary) > 900:
            summary = summary[:900].rsplit(" ", 1)[0] + "…"
        absent = [k for k in ("corp", "family", "coop", "nonprofit", "pub")
                  if not counts.get(k)]
        stories.append({
            "id": sid,
            "topic": classify_topic(topic_src),
            "summary": summary,
            "summaryFrom": summary_from,
            "emphasis": emphasis(arts, outlets),
            "absent": absent,
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


def _x(t):
    """escape text for XML"""
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def own_sentence(story, outlets):
    parts = []
    for k, label in (("corp", "corporate"), ("family", "billionaire/family"),
                     ("coop", "worker-owned"), ("nonprofit", "nonprofit"), ("pub", "public")):
        n = story["counts"].get(k, 0)
        if n:
            parts.append(f"{n} {label}")
    return "Covered by " + ", ".join(parts) + "."


def write_rss(path, title, desc, stories, outlets):
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for st in stories:
        pub = datetime.fromisoformat(st["updated"]).strftime("%a, %d %b %Y %H:%M:%S +0000")
        lead = st["articles"][0]
        body = st.get("summary") or ""
        desc_txt = (f"{body}<br><br>" if body else "") + _x(own_sentence(st, outlets)) + \
                   "<br>Sources: " + ", ".join(
                       sorted({outlets[a["outlet"]]["name"] for a in st["articles"]}))
        items.append(f"""  <item>
    <title>{_x(st['headline'])}</title>
    <link>{_x(SITE_URL)}#s/{st['id']}</link>
    <guid isPermaLink="false">lede-{st['id']}</guid>
    <pubDate>{pub}</pubDate>
    <category>{_x(st.get('topic') or 'Other')}</category>
    <description>{_x(desc_txt)}</description>
  </item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="feed.xsl"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{_x(title)}</title>
  <link>{_x(SITE_URL)}</link>
  <atom:link href="{_x(SITE_URL + path.name)}" rel="self" type="application/rss+xml"/>
  <description>{_x(desc)}</description>
  <language>en</language>
  <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
"""
    path.write_text(xml)


def update_history(stories, outlets):
    """Append one snapshot per day of how concentrated coverage was."""
    try:
        hist = json.loads(HIST_OUT.read_text())
    except Exception:
        hist = {"note": "Daily snapshot of coverage share by ownership class.", "days": []}
    totals, total = {}, 0
    for st in stories:
        for k, n in st["counts"].items():
            totals[k] = totals.get(k, 0) + n
            total += n
    if not total:
        return hist
    today = datetime.now(timezone.utc).date().isoformat()
    entry = {
        "date": today,
        "articles": total,
        "stories": len(stories),
        "share": {k: round(v / total * 100, 1) for k, v in totals.items()},
    }
    days = [d for d in hist.get("days", []) if d.get("date") != today]
    days.append(entry)
    days.sort(key=lambda d: d["date"])
    hist["days"] = days[-400:]          # a bit over a year
    hist["updated"] = datetime.now(timezone.utc).isoformat()
    HIST_OUT.write_text(json.dumps(hist, indent=1))
    return hist


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

    write_rss(FEED_OUT, "Lede — all stories",
              "News grouped by who owns the outlets covering it.", stories, outlets)
    under = [s2 for s2 in stories if s2.get("underreported") and s2["outletCount"] >= 2]
    write_rss(UNDER_OUT, "Lede — underreported",
              "Stories whose coverage is concentrated outside corporate and billionaire-owned media.",
              under, outlets)
    hist = update_history(stories, outlets)
    print(f"wrote feed.xml ({len(stories)}), underreported.xml ({len(under)}), "
          f"history.json ({len(hist.get('days', []))} days)", file=sys.stderr)


if __name__ == "__main__":
    main()
