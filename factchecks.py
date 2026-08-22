#!/usr/bin/env python3
"""
Lede: fact-check tallies for public figures quoted in the news.

Pulls recent fact-checks from the Google Fact Check Tools API — which aggregates
ClaimReview data that PolitiFact, FactCheck.org, Snopes, AFP and others publish
specifically for machine reading — and aggregates them per claimant.

Deliberate design choices:
  * The roster is NOT curated by us. We pull whatever fact-checkers recently
    published, so who appears is decided by their editorial choices, not ours.
  * We store tallies and links, never the fact-checkers' article text.
  * We rate PEOPLE MAKING CLAIMS IN THE NEWS, never the reporters covering them.
    Fact-checkers do not meaningfully check working reporters, so any such score
    would be built on a sample of one or two.

Usage:
    GOOGLE_FACTCHECK_KEY=... python factchecks.py       # live
    python factchecks.py --mock                          # offline test data

Without a key it exits 0 quietly and the site simply omits the feature.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "factchecks.json"
API = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# Publishers to harvest from. Pulling per-publisher rather than by search term
# keeps the roster driven by what they chose to check.
PUBLISHERS = [
    "politifact.com", "factcheck.org", "snopes.com", "apnews.com",
    "usatoday.com", "fullfact.org", "checkyourfact.com", "leadstories.com",
    "africacheck.org", "factcheck.afp.com",
]
MAX_AGE_DAYS = 1460          # ~4 years
PAGES_PER_PUBLISHER = 10     # x100 results
MIN_CHECKS = 5               # below this a tally is noise, not a signal

# --- rating normalisation -------------------------------------------------
# textualRating is free text and varies by publisher: "Pants on Fire!",
# "Four Pinocchios", "Mostly false", "Misleading". Map onto five buckets.
RATING_RULES = [
    ("false",  [r"pants on fire", r"four pinocchio", r"^false", r"\bfalse\b",
                r"incorrect", r"fabricat", r"no evidence", r"debunk", r"hoax",
                r"scam", r"fake", r"three pinocchio"]),
    ("mostly-false", [r"mostly false", r"largely false", r"misleading",
                      r"missing context", r"exaggerat", r"distort", r"two pinocchio",
                      r"partly false", r"mostly untrue"]),
    ("mixed", [r"half true", r"half-true", r"mixture", r"mixed", r"partly true",
               r"in between", r"one pinocchio", r"unproven", r"unsupported",
               r"outdated", r"needs context"]),
    ("mostly-true", [r"mostly true", r"largely true", r"mostly accurate",
                     r"mostly correct", r"geppetto"]),
    ("true", [r"^true", r"\btrue\b", r"accurate", r"correct", r"verified", r"^fact$"]),
]


def normalise_rating(text):
    t = (text or "").strip().lower()
    if not t:
        return None
    # order matters: check the more specific compounds before the bare words
    for bucket in ("mostly-false", "mostly-true", "mixed", "false", "true"):
        for name, pats in RATING_RULES:
            if name != bucket:
                continue
            for p in pats:
                if re.search(p, t):
                    return bucket
    return None


FALSEY = {"false", "mostly-false"}


def api_page(key, publisher, page_token=None):
    params = {
        "key": key,
        "reviewPublisherSiteFilter": publisher,
        "pageSize": 100,
        "maxAgeDays": MAX_AGE_DAYS,
        "languageCode": "en",
    }
    if page_token:
        params["pageToken"] = page_token
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def harvest(key):
    claims = []
    for pub in PUBLISHERS:
        token, pages = None, 0
        while pages < PAGES_PER_PUBLISHER:
            try:
                data = api_page(key, pub, token)
            except Exception as ex:
                print(f"  {pub}: {ex}", file=sys.stderr)
                break
            got = data.get("claims", [])
            claims.extend(got)
            token = data.get("nextPageToken")
            pages += 1
            if not token or not got:
                break
            time.sleep(0.2)
        print(f"  {pub}: {sum(1 for c in claims)} cumulative", file=sys.stderr)
    return claims


def aggregate(claims):
    people = {}
    for c in claims:
        who = (c.get("claimant") or "").strip()
        # Skip non-person claimants: viral posts, chain emails, anonymous sources.
        if not who or len(who) > 60:
            continue
        low = who.lower()
        if any(w in low for w in ("posts", "post", "bloggers", "chain email", "viral",
                                  "users", "video", "meme", "tiktok", "facebook",
                                  "instagram", "threads", "website", "websites",
                                  "social media", "multiple sources", "various")):
            continue
        for rev in c.get("claimReview", []) or []:
            bucket = normalise_rating(rev.get("textualRating"))
            if not bucket:
                continue
            p = people.setdefault(who, {
                "name": who, "counts": {}, "publishers": {},
                "latest": None, "sample": []})
            p["counts"][bucket] = p["counts"].get(bucket, 0) + 1
            pubname = ((rev.get("publisher") or {}).get("name")
                       or (rev.get("publisher") or {}).get("site") or "?")
            p["publishers"][pubname] = p["publishers"].get(pubname, 0) + 1
            d = rev.get("reviewDate") or ""
            if d and (not p["latest"] or d > p["latest"]):
                p["latest"] = d
            if len(p["sample"]) < 3 and rev.get("url"):
                p["sample"].append({
                    "text": (c.get("text") or "")[:200],
                    "rating": rev.get("textualRating"),
                    "publisher": pubname,
                    "url": rev.get("url"),
                    "date": d[:10],
                })
    out = {}
    for name, p in people.items():
        total = sum(p["counts"].values())
        if total < MIN_CHECKS:
            continue
        falsey = sum(n for b, n in p["counts"].items() if b in FALSEY)
        p["total"] = total
        p["falseShare"] = round(falsey / total * 100)
        p["publishers"] = dict(sorted(p["publishers"].items(),
                                      key=lambda kv: -kv[1])[:4])
        out[name] = p
    return out


def mock_claims():
    """Offline sample shaped exactly like the API response."""
    def mk(who, text, rating, pub, url, date):
        return {"text": text, "claimant": who,
                "claimReview": [{"textualRating": rating,
                                 "publisher": {"name": pub, "site": pub.lower() + ".com"},
                                 "url": url, "reviewDate": date}]}
    rows = []
    for i, r in enumerate(["False", "Pants on Fire!", "Mostly False", "Half True",
                           "False", "Mostly True", "False", "Four Pinocchios"]):
        rows.append(mk("Example Senator", f"Claim number {i} about the budget.", r,
                       "PolitiFact", f"https://politifact.com/x{i}", f"2026-0{i%9+1}-14"))
    for i, r in enumerate(["True", "Mostly True", "True", "Half True", "Mostly True"]):
        rows.append(mk("Example Governor", f"Statement {i} on school funding.", r,
                       "FactCheck.org", f"https://factcheck.org/y{i}", f"2026-0{i%9+1}-02"))
    for i, r in enumerate(["False", "Misleading", "True"]):   # below MIN_CHECKS
        rows.append(mk("Rarely Checked Person", f"Minor claim {i}.", r,
                       "Snopes", f"https://snopes.com/z{i}", "2025-11-01"))
    rows.append(mk("Viral image posts", "A viral claim.", "False", "Snopes",
                   "https://snopes.com/v1", "2026-01-01"))   # should be filtered out
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="use offline sample data")
    ap.add_argument("--force", action="store_true", help="refresh even if data is fresh")
    args = ap.parse_args()

    # Tallies move slowly and the API has a daily quota: refresh about once a day.
    if not args.force and OUT.exists():
        try:
            age_h = (time.time() - OUT.stat().st_mtime) / 3600
            if age_h < 20:
                print(f"factchecks: data is {age_h:.1f}h old — skipping refresh.", file=sys.stderr)
                return
        except OSError:
            pass

    key = os.environ.get("GOOGLE_FACTCHECK_KEY", "").strip()
    if not key and not args.mock:
        print("factchecks: GOOGLE_FACTCHECK_KEY not set — skipping (site still works).",
              file=sys.stderr)
        return

    claims = mock_claims() if args.mock else harvest(key)
    print(f"factchecks: {len(claims)} claims fetched", file=sys.stderr)
    people = aggregate(claims)

    OUT.write_text(json.dumps({
        "generated": datetime.now(timezone.utc).isoformat(),
        "source": ("Google Fact Check Tools API, aggregating ClaimReview data "
                   "published by fact-checking organisations."),
        "note": ("Tallies count claims these people made in public that fact-checkers "
                 "chose to examine — not reporters' work, and not a sample of "
                 "everything they have said."),
        "minChecks": MIN_CHECKS,
        "people": people,
    }, indent=1))
    print(f"factchecks: {len(people)} people with {MIN_CHECKS}+ checks -> {OUT}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
