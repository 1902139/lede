# Lede

**Live at:** https://joelbarandi.github.io/lede/

A small news aggregator built around one idea: instead of rating outlets "left"
or "right," show **who owns them, what else the owner holds, and how the money
flows** — then link straight to the original articles so people judge for
themselves.

Live pieces: RSS aggregation from ~20 outlets across five ownership classes
(corporate, billionaire/family, worker-owned, nonprofit, public), same-story
clustering, news/opinion separation, an "Underreported" view for stories thin
on corporate coverage, and a curated ownership file for every outlet.

## Put it online

**→ Follow [SETUP.md](SETUP.md) for the complete click-by-click walkthrough.**

Short version: create a public GitHub repo, upload these files, enable
read/write workflow permissions, run the "Update stories" Action once, and
turn on GitHub Pages. Your site lands at
`https://<your-username>.github.io/lede/` and refreshes itself hourly, free,
with no server.

Optional Stage 2 (article analysis + author pattern profiles) needs an
Anthropic API key stored as the repo secret `ANTHROPIC_API_KEY` — roughly
$0.10–$2.00/month at this scale. Without it, the analysis step skips itself
and everything else works.

## Run it locally

```bash
pip install feedparser
python fetch_news.py        # fetches feeds, writes data/stories.json
python -m http.server               # then open http://localhost:8000
```

(Opening index.html by double-click won't load data — browsers block local
fetches. Use the little server line above.)

## Things worth knowing

- **Feeds fail sometimes.** The header badge shows how many feeds responded on
  the last run (`14/34 feeds`). A failing feed just means that outlet is absent
  until it recovers; the fetcher logs failures in the Action output. Feed URLs
  live in `ownership.json` — fix or swap them there.
- **AP and Reuters are missing** because they no longer publish usable public
  RSS feeds. Their coverage often arrives indirectly via outlets that carry
  wire stories.
- **Clustering is heuristic.** Same-story grouping matches title words; it's
  right most of the time and imperfect by nature. Tune `JACCARD_JOIN` /
  `SHARED_JOIN` in `fetch_news.py` if it splits or merges too eagerly.
- **The ownership database is the editorial product.** `ownership.json`
  is hand-curated from public records and deliberately simplified. Review it
  a couple of times a year; ownership changes are rare but real.
- **Legal posture:** the site shows headlines and links out — full text stays
  with the publishers. That's standard aggregator practice. (Not legal advice.)

## Stage 2 — article analysis (built, opt-in)

`analyze.py` sends each new article's headline + RSS summary to the
Claude API and gets back: what the piece actually is (news / opinion /
analysis / press-release, regardless of how the outlet labels it), headline
framing flags, and which source types it leans on. Results are cached by URL
so each article costs money exactly once. Bylines with 3+ analyzed pieces get
a **pattern profile** — opinion ratio, framing-flag rate, and source mix.

**No factuality scores, by design.** Verifying claims against primary sources
credibly requires human review. An automated factuality percentage would be
precisely the opaque rating this project exists to replace, so the author
files show observable patterns with their evidence instead.

Test it without an API key: `python analyze.py --mock`

## Roadmap (stage 3)

Human-reviewed claim checks on major stories; headline-vs-body divergence
(needs article text, so it needs care around fair use); reader-submitted
ownership corrections.
