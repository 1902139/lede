#!/usr/bin/env python3
"""
Lede Stage 2: article-level analysis via the Claude API.

Reads data/stories.json (produced by fetch_news.py), sends each NEW article's
headline + RSS summary to the Claude API for classification, caches results by
URL, merges them back into stories.json, and rebuilds data/authors.json
(per-author pattern profiles).

What this does NOT do, on purpose: assign factuality scores. Verifying claims
against primary sources credibly requires human review; automated "factuality"
would be exactly the kind of black-box rating this project exists to replace.

Usage:
    ANTHROPIC_API_KEY=sk-... python analyze.py     # real analysis
    python analyze.py --mock                        # deterministic fake analysis (testing)

If ANTHROPIC_API_KEY is unset (and --mock not given), exits 0 quietly so the
site keeps working without Stage 2.
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STORIES = ROOT / "stories.json"
CACHE = ROOT / "analysis_cache.json"
AUTHORS = ROOT / "authors.json"

MODEL = "claude-haiku-4-5"       # cheap + plenty for classification; change if needed
MAX_NEW_PER_RUN = 120            # cost guard per run
MAX_CACHE = 3000                 # keep this many most-recent entries
API_URL = "https://api.anthropic.com/v1/messages"

KINDS = ["news", "opinion", "analysis", "press-release"]
FLAGS = ["sensational", "editorializing", "vague-attribution", "question-headline"]
SOURCES = ["officials", "business", "workers-or-affected", "independent-experts", "documents"]

PROMPT = """You are classifying news articles from their headline and RSS summary only.
For each numbered item, return a JSON object with:
- "kind": one of {kinds} (what the piece IS, regardless of how the outlet labels it)
- "flags": array, subset of {flags} describing the HEADLINE (empty array if the headline is neutral)
- "sources": array, subset of {sources} — the source types the text indicates are quoted or relied on (empty if unclear)

Be conservative: only flag what is clearly present. Summaries are partial; when unsure, use empty arrays.
Return ONLY a JSON array, one object per item, in order. No other text.

Items:
{items}"""


def load(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def call_claude(api_key, items):
    body = {
        "model": MODEL,
        "max_tokens": 1500,
        "messages": [{
            "role": "user",
            "content": PROMPT.format(
                kinds=json.dumps(KINDS), flags=json.dumps(FLAGS), sources=json.dumps(SOURCES),
                items="\n".join(
                    f'{i+1}. HEADLINE: {a["title"]}\n   SUMMARY: {(a.get("summary") or "(none)")[:400]}'
                    for i, a in enumerate(items)))
        }],
    }
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(),
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.load(r)
    text = "".join(b.get("text", "") for b in resp.get("content", []))
    # tolerate stray text around the JSON array
    start, end = text.find("["), text.rfind("]")
    parsed = json.loads(text[start:end + 1])
    out = []
    for p in parsed:
        out.append({
            "kind": p.get("kind") if p.get("kind") in KINDS else None,
            "flags": [f for f in p.get("flags", []) if f in FLAGS],
            "sources": [s for s in p.get("sources", []) if s in SOURCES],
        })
    return out


def mock_analysis(a):
    """Deterministic fake analysis so the pipeline/UI can be tested without a key."""
    h = int(hashlib.md5(a["url"].encode()).hexdigest(), 16)
    return {
        "kind": "opinion" if a.get("kind") == "opinion" else ("analysis" if h % 7 == 0 else "news"),
        "flags": (["sensational"] if h % 3 == 0 else []) + (["vague-attribution"] if h % 5 == 0 else []),
        "sources": [SOURCES[h % len(SOURCES)], SOURCES[(h >> 4) % len(SOURCES)]][: 1 + h % 2],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="fake analysis for local testing")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key and not args.mock:
        print("analyze: ANTHROPIC_API_KEY not set — skipping Stage 2 (site still works).", file=sys.stderr)
        return

    data = load(STORIES, None)
    if not data or not data.get("stories"):
        print("analyze: no stories.json yet — run fetch_news.py first.", file=sys.stderr)
        return
    cache = load(CACHE, {})

    # collect articles needing analysis
    todo = []
    for s in data["stories"]:
        for a in s["articles"]:
            if a["url"] not in cache:
                todo.append(a)
    todo = todo[:MAX_NEW_PER_RUN]
    print(f"analyze: {len(todo)} new articles to analyze", file=sys.stderr)

    # analyze in batches of 8
    failed = 0
    for i in range(0, len(todo), 8):
        batch = todo[i:i + 8]
        try:
            results = ([mock_analysis(a) for a in batch] if args.mock
                       else call_claude(api_key, batch))
            if len(results) != len(batch):
                raise ValueError(f"expected {len(batch)} results, got {len(results)}")
        except Exception as ex:
            failed += len(batch)
            print(f"analyze: batch failed ({ex}) — skipping", file=sys.stderr)
            continue
        now = datetime.now(timezone.utc).isoformat()
        for a, r in zip(batch, results):
            cache[a["url"]] = {**r, "author": a.get("author"), "outlet": a["outlet"],
                               "feedKind": a.get("kind"), "ts": now}
        if not args.mock:
            time.sleep(1)  # gentle pacing

    # trim cache to most recent entries
    if len(cache) > MAX_CACHE:
        keep = sorted(cache.items(), key=lambda kv: kv[1].get("ts", ""), reverse=True)[:MAX_CACHE]
        cache = dict(keep)
    CACHE.write_text(json.dumps(cache, indent=1))

    # merge analysis into stories.json
    for s in data["stories"]:
        for a in s["articles"]:
            c = cache.get(a["url"])
            if c:
                a["analysis"] = {"kind": c["kind"], "flags": c["flags"], "sources": c["sources"]}
        # recount news/opinion using analyzed kind where available
        s["newsCount"] = sum(1 for a in s["articles"]
                             if (a.get("analysis", {}).get("kind") or a["kind"]) == "news")
        s["opinionCount"] = sum(1 for a in s["articles"]
                                if (a.get("analysis", {}).get("kind") or a["kind"]) in ("opinion", "press-release"))
    data["analyzed"] = True
    STORIES.write_text(json.dumps(data, indent=1))

    # rebuild author pattern profiles from the whole cache
    authors = {}
    for url, c in cache.items():
        name = (c.get("author") or "").strip()
        if not name or len(name) > 60:
            continue
        key = f"{name}|{c['outlet']}"
        rec = authors.setdefault(key, {"name": name, "outlet": c["outlet"], "pieces": 0,
                                       "opinion": 0, "flagged": 0,
                                       "sources": {k: 0 for k in SOURCES}})
        rec["pieces"] += 1
        if (c.get("kind") or c.get("feedKind")) in ("opinion", "press-release"):
            rec["opinion"] += 1
        if c.get("flags"):
            rec["flagged"] += 1
        for src in c.get("sources", []):
            rec["sources"][src] += 1
    AUTHORS.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(),
        "note": "Pattern profiles from automated reads of headlines/summaries. No factuality scores — claim verification needs human review.",
        "authors": {k: v for k, v in authors.items()},
    }, indent=1))

    print(f"analyze: done — cache {len(cache)}, authors {len(authors)}, failed {failed}", file=sys.stderr)


if __name__ == "__main__":
    main()
