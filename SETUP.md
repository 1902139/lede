<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lede — who owns your news</title>
<style>
  :root {
    color-scheme: light;
    --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e;
    --muted: #898781; --grid: #e1e0d9; --baseline: #c3c2b7; --ring: rgba(11,11,11,0.10);
    --own-corp: #2a78d6; --own-family: #eb6834; --own-coop: #1baf7a;
    --own-nonprofit: #eda100; --own-public: #e87ba4;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; background: var(--page); color: var(--ink); font-size: 15px; line-height: 1.5; }
  a { color: inherit; }
  header { background: var(--surface); border-bottom: 1px solid var(--grid); position: sticky; top: 0; z-index: 20; }
  .header-inner { max-width: 980px; margin: 0 auto; padding: 14px 20px 0; }
  .header-top { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
  .wordmark { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
  .wordmark span { color: var(--own-corp); }
  .tagline { color: var(--ink-2); font-size: 13.5px; }
  .gen-badge { margin-left: auto; font-size: 11.5px; font-weight: 600; color: var(--ink-2); background: var(--page); border: 1px solid var(--grid); border-radius: 99px; padding: 3px 10px; white-space: nowrap; }
  nav { display: flex; gap: 2px; margin-top: 10px; }
  nav button { appearance: none; border: none; background: none; cursor: pointer; font: inherit; font-weight: 600; font-size: 14px; color: var(--ink-2); padding: 9px 14px; border-bottom: 2.5px solid transparent; }
  nav button:hover { color: var(--ink); background: var(--page); border-radius: 6px 6px 0 0; }
  nav button.active { color: var(--ink); border-bottom-color: var(--ink); }
  main { max-width: 980px; margin: 0 auto; padding: 26px 20px 60px; }
  .view { display: none; } .view.active { display: block; }
  .view-intro { color: var(--ink-2); font-size: 14px; max-width: 68ch; margin-bottom: 18px; }
  .view-intro strong { color: var(--ink); }
  h2.view-title { font-size: 19px; margin-bottom: 6px; letter-spacing: -0.2px; }
  .card { background: var(--surface); border: 1px solid var(--ring); border-radius: 12px; padding: 18px 20px; margin-bottom: 16px; }
  .card.clickable { cursor: pointer; transition: border-color .12s, box-shadow .12s; }
  .card.clickable:hover { border-color: var(--baseline); box-shadow: 0 2px 10px rgba(11,11,11,0.06); }
  .story-meta { display: flex; gap: 10px; align-items: center; font-size: 12px; color: var(--muted); margin-bottom: 6px; }
  .story-h { font-size: 17px; font-weight: 700; letter-spacing: -0.2px; line-height: 1.35; }
  .own-bar-wrap { margin-top: 13px; }
  .own-bar-label { font-size: 11.5px; font-weight: 600; color: var(--muted); margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.4px; }
  .own-bar { display: flex; height: 14px; border-radius: 4px; overflow: hidden; background: var(--page); }
  .own-bar .seg { border-right: 2px solid var(--surface); }
  .own-bar .seg:last-child { border-right: none; }
  .own-legend { display: flex; flex-wrap: wrap; gap: 5px 14px; margin: 0 0 16px; font-size: 12px; color: var(--ink-2); }
  .own-legend .li { display: flex; align-items: center; gap: 5px; }
  .dot { width: 9px; height: 9px; border-radius: 50%; flex: none; }
  .chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
  .chip { font-size: 12px; font-weight: 600; color: var(--ink-2); background: var(--page); border: 1px solid var(--grid); border-radius: 99px; padding: 3px 10px; }
  .chip.alert { color: #8a4a12; background: #fdf3ea; border-color: #f3ddc8; }
  .back-btn { appearance: none; border: 1px solid var(--grid); background: var(--surface); font: inherit; font-size: 13px; font-weight: 600; color: var(--ink-2); border-radius: 8px; padding: 6px 12px; cursor: pointer; margin-bottom: 18px; }
  .back-btn:hover { color: var(--ink); border-color: var(--baseline); }
  .article-row { background: var(--surface); border: 1px solid var(--ring); border-radius: 10px; margin-bottom: 10px; overflow: hidden; }
  .article-main { padding: 13px 16px; cursor: pointer; }
  .article-main:hover { background: var(--page); }
  .a-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
  .a-outlet { font-weight: 700; font-size: 13.5px; }
  .type-tag { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 4px; padding: 2px 6px; }
  .type-news { background: #e9f1fb; color: #1c5cab; }
  .type-opinion { background: #f4eef8; color: #6b4a8f; }
  .a-own { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--ink-2); }
  .a-by { margin-left: auto; font-size: 12px; color: var(--muted); white-space: nowrap; }
  .byline { margin-left: auto; font-size: 12px; color: var(--ink-2); font-weight: 600; background: var(--page); border: 1px solid var(--grid); border-radius: 99px; padding: 2px 10px; cursor: pointer; white-space: nowrap; }
  .byline:hover { color: var(--ink); border-color: var(--baseline); }
  .a-chips { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }
  .a-chips .chip { font-size: 11px; padding: 2px 8px; }
  .author-panel { display: none; border-top: 1px solid var(--grid); background: var(--page); padding: 14px 16px; }
  .article-row.open-author .author-panel { display: block; }
  .author-panel h5 { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--muted); margin: 12px 0 5px; }
  .author-panel h5:first-child { margin-top: 0; }
  .ap-head { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
  .ap-name { font-weight: 700; font-size: 14px; }
  .ap-role { font-size: 12px; color: var(--muted); }
  .mb-row { display: flex; align-items: center; gap: 10px; font-size: 12.5px; margin-top: 5px; }
  .mb-name { width: 160px; flex: none; color: var(--ink-2); }
  .mb-track { flex: 1; max-width: 260px; height: 10px; background: var(--surface); border: 1px solid var(--grid); border-radius: 4px; overflow: hidden; }
  .mb-fill { height: 100%; background: var(--own-corp); border-radius: 3px; }
  .mb-val { width: 44px; flex: none; color: var(--ink-2); font-variant-numeric: tabular-nums; }
  .ap-note { font-size: 11.5px; color: var(--muted); margin-top: 10px; }
  .a-head { font-size: 14px; line-height: 1.4; }
  .a-head a { text-decoration: none; }
  .a-head a:hover { text-decoration: underline; }
  .a-head .ext { font-size: 11px; color: var(--muted); }
  .a-expand-hint { font-size: 11.5px; color: var(--muted); margin-top: 6px; }
  .own-panel { display: none; border-top: 1px solid var(--grid); background: var(--page); padding: 14px 16px; }
  .article-row.open .own-panel { display: block; }
  .own-panel h5 { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--muted); margin: 12px 0 5px; }
  .own-panel h5:first-child { margin-top: 0; }
  .own-panel p { font-size: 13px; color: var(--ink-2); }
  .chain { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: 13px; }
  .chain .node { background: var(--surface); border: 1px solid var(--grid); border-radius: 6px; padding: 3px 9px; font-weight: 600; }
  .chain .arrow { color: var(--muted); }
  .why-box { background: var(--page); border: 1px solid var(--grid); border-radius: 8px; padding: 10px 14px; margin-top: 12px; font-size: 13px; color: var(--ink-2); }
  .why-box b { color: var(--ink); }
  .outlet-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 14px; }
  .outlet-card h3 { font-size: 15.5px; display: flex; align-items: center; gap: 8px; }
  .outlet-card h3 a { text-decoration: none; }
  .outlet-card h3 a:hover { text-decoration: underline; }
  .outlet-card .o-sub { font-size: 12.5px; color: var(--muted); margin: 2px 0 10px; }
  .outlet-card h5 { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--muted); margin: 10px 0 4px; }
  .outlet-card p { font-size: 13px; color: var(--ink-2); }
  .method-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  @media (max-width: 700px) { .method-grid { grid-template-columns: 1fr; } }
  .method-card h3 { font-size: 15px; margin-bottom: 6px; }
  .method-card p { font-size: 13.5px; color: var(--ink-2); }
  .method-card .vs { font-size: 12px; font-weight: 700; color: #d03b3b; text-transform: uppercase; letter-spacing: 0.4px; }
  .method-card .soon { font-size: 12px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.4px; }
  .empty { text-align: center; color: var(--ink-2); padding: 40px 20px; font-size: 14px; }
  footer { border-top: 1px solid var(--grid); margin-top: 40px; padding: 18px 20px; }
  .footer-inner { max-width: 980px; margin: 0 auto; font-size: 12.5px; color: var(--muted); }
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="header-top">
      <div class="wordmark">Lede<span>.</span></div>
      <div class="tagline">Who owns your news — and how the money flows.</div>
      <div class="gen-badge" id="gen-badge">loading…</div>
    </div>
    <nav id="nav"></nav>
  </div>
</header>
<main>
  <section class="view" id="view-feed"><div class="empty">Loading stories…</div></section>
  <section class="view" id="view-detail"></section>
  <section class="view" id="view-under"></section>
  <section class="view" id="view-outlets"></section>
  <section class="view" id="view-about"></section>
</main>
<footer>
  <div class="footer-inner">
    Lede aggregates headlines via public RSS feeds and links to the original articles — full text stays with
    the publishers. Ownership notes are curated from public records (simplified; corrections welcome).
    No left–right scores, no investors, no ads. Inspired by the critique in
    "Ground News and the War on Reality" (Literate Machine, 2026).
  </div>
</footer>
<script>
const OWN_TYPES = {
  corp:      { label: "Corporate", color: "var(--own-corp)" },
  family:    { label: "Billionaire / family", color: "var(--own-family)" },
  coop:      { label: "Worker-owned", color: "var(--own-coop)" },
  nonprofit: { label: "Nonprofit", color: "var(--own-nonprofit)" },
  pub:       { label: "Public / state", color: "var(--own-public)" }
};
const ORDER = ["corp","family","coop","nonprofit","pub"];
const $ = (s, el=document) => el.querySelector(s);
const esc = s => String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;");
let OUTLETS = {}, STORIES = [], GENERATED = null, AUTHORS = {};

const FLAG_LABELS = {
  "sensational": "sensational headline",
  "editorializing": "editorializing headline",
  "vague-attribution": "vague attribution",
  "question-headline": "question headline"
};
const SOURCE_LABELS = {
  "officials": "Officials",
  "business": "Business / industry",
  "workers-or-affected": "Workers / affected",
  "independent-experts": "Independent experts",
  "documents": "Documents / filings"
};

function authorRec(name, outlet) {
  const r = AUTHORS[`${name}|${outlet}`];
  return (r && r.pieces >= 3) ? r : null;
}
function authorPanelHTML(r) {
  const oPct = Math.round(r.opinion / r.pieces * 100);
  const fPct = Math.round(r.flagged / r.pieces * 100);
  const srcTotal = Object.values(r.sources).reduce((a,b)=>a+b,0) || 1;
  return `<div class="author-panel">
    <div class="ap-head"><span class="ap-name">${esc(r.name)}</span>
      <span class="ap-role">${esc(OUTLETS[r.outlet]?.name || r.outlet)} · ${r.pieces} pieces tracked</span></div>
    <h5>Pattern profile</h5>
    <p style="font-size:13px;color:var(--ink-2)">${oPct}% opinion pieces · ${fPct}% of headlines carried a framing flag</p>
    <h5>Source types their pieces lean on</h5>
    ${Object.entries(r.sources).filter(([,n])=>n>0).sort((a,b)=>b[1]-a[1]).map(([k,n]) => `
      <div class="mb-row"><span class="mb-name">${SOURCE_LABELS[k]}</span>
      <div class="mb-track"><div class="mb-fill" style="width:${Math.round(n/srcTotal*100)}%"></div></div>
      <span class="mb-val">${Math.round(n/srcTotal*100)}%</span></div>`).join("") || `<p style="font-size:13px;color:var(--muted)">Not enough data yet.</p>`}
    <p class="ap-note">Automated pattern profile from headlines and summaries — evidence of tendencies, not a verdict.
    No factuality score: claim verification needs human review, and we won't fake it.</p></div>`;
}

function ago(iso) {
  const m = (Date.now() - new Date(iso).getTime()) / 60000;
  if (m < 60) return `${Math.max(1, Math.round(m))}m ago`;
  if (m < 60*24) return `${Math.round(m/60)}h ago`;
  return `${Math.round(m/1440)}d ago`;
}
const ownDot = t => `<span class="dot" style="background:${OWN_TYPES[t].color}"></span>`;

function ownBar(counts) {
  const total = Object.values(counts).reduce((a,b)=>a+b,0);
  let segs = "";
  for (const key of ORDER) {
    const n = counts[key] || 0;
    if (!n) continue;
    segs += `<div class="seg" style="width:${(n/total*100).toFixed(1)}%;background:${OWN_TYPES[key].color}" title="${OWN_TYPES[key].label}: ${n}"></div>`;
  }
  return `<div class="own-bar-wrap">
    <div class="own-bar-label">Who owns this coverage — ${total} article${total>1?"s":""}</div>
    <div class="own-bar">${segs}</div></div>`;
}
function ownLegendAll() {
  return `<div class="own-legend">` + ORDER.map(k =>
    `<span class="li">${ownDot(k)}${OWN_TYPES[k].label}</span>`).join("") + `</div>`;
}
function chipRow(s) {
  let c = `<span class="chip">${s.newsCount} news · ${s.opinionCount} opinion</span>`;
  if (s.underreported) c += `<span class="chip alert">⚠ thin corporate coverage</span>`;
  return `<div class="chip-row">${c}</div>`;
}

function storyCard(s) {
  return `<article class="card clickable" onclick="openStory('${s.id}')">
    <div class="story-meta"><span>${s.outletCount} outlet${s.outletCount>1?"s":""}</span><span>${ago(s.updated)}</span></div>
    <div class="story-h">${esc(s.headline)}</div>
    ${ownBar(s.counts)}${chipRow(s)}</article>`;
}

function renderFeed() {
  const multi = STORIES.filter(s => s.outletCount >= 2);
  const single = STORIES.filter(s => s.outletCount === 1).slice(0, 10);
  $("#view-feed").innerHTML = `
    <h2 class="view-title">Top stories</h2>
    <p class="view-intro">No left–right bar. Each story shows <strong>who owns the outlets covering it</strong>.
    Headlines link to the original articles.</p>
    ${ownLegendAll()}
    ${multi.length ? multi.map(storyCard).join("") : `<div class="empty">No multi-outlet stories in the current window.</div>`}
    ${single.length ? `<h2 class="view-title" style="margin-top:26px">More from single outlets</h2>` + single.map(storyCard).join("") : ""}`;
}

function ownPanel(o) {
  return `<div class="own-panel">
    <h5>Ownership chain</h5>
    <div class="chain">${o.chain.map((n,j)=>`<span class="node">${esc(n)}</span>${j<o.chain.length-1?`<span class="arrow">→</span>`:""}`).join("")}</div>
    <h5>Other holdings</h5><p>${esc(o.holdings)}</p>
    <h5>Funding model</h5><p>${esc(o.funding)}</p></div>`;
}

function openStory(id) {
  const s = STORIES.find(x => x.id === id);
  if (!s) return;
  $("#view-detail").innerHTML = `
    <button class="back-btn" onclick="show('feed')">← All stories</button>
    <div class="story-meta"><span>${s.outletCount} outlet${s.outletCount>1?"s":""}</span><span>${ago(s.updated)}</span></div>
    <h2 class="view-title" style="font-size:21px">${esc(s.headline)}</h2>
    ${ownBar(s.counts)}${chipRow(s)}
    <div style="height:16px"></div>
    ${s.articles.map((a,i) => {
      const o = OUTLETS[a.outlet];
      const an = a.analysis || null;
      const kind = (an && an.kind) || a.kind;
      const rec = a.author ? authorRec(a.author, a.outlet) : null;
      const byline = !a.author ? "" :
        rec ? `<span class="byline" onclick="event.stopPropagation();document.getElementById('ar-${i}').classList.toggle('open-author')">${esc(a.author)} · ${rec.pieces} tracked ▾</span>`
            : `<span class="a-by">${esc(a.author)}</span>`;
      const chips = an ? [
        ...an.flags.map(f => `<span class="chip alert">⚠ ${FLAG_LABELS[f] || f}</span>`),
        ...(an.sources.length ? [`<span class="chip">quotes: ${an.sources.map(s2 => (SOURCE_LABELS[s2]||s2).toLowerCase()).join(", ")}</span>`] : [])
      ].join("") : "";
      return `<div class="article-row" id="ar-${i}">
        <div class="article-main" onclick="document.getElementById('ar-${i}').classList.toggle('open')">
          <div class="a-top">
            <span class="a-outlet">${esc(o.name)}</span>
            <span class="type-tag ${kind==="news"?"type-news":"type-opinion"}">${kind}</span>
            <span class="a-own">${ownDot(o.type)}${OWN_TYPES[o.type].label}</span>
            ${byline}
          </div>
          <div class="a-head"><a href="${esc(a.url)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">“${esc(a.title)}” <span class="ext">↗</span></a></div>
          ${chips ? `<div class="a-chips">${chips}</div>` : ""}
          <div class="a-expand-hint">Ownership file ▾ · ${ago(a.published)}</div>
        </div>
        ${rec ? authorPanelHTML(rec) : ""}
        ${ownPanel(o)}</div>`;
    }).join("")}`;
  show("detail");
  window.scrollTo(0,0);
}

function renderUnder() {
  const list = STORIES.filter(s => s.underreported && s.outletCount >= 2);
  $("#view-under").innerHTML = `
    <h2 class="view-title">Underreported</h2>
    <p class="view-intro">Stories whose coverage is <strong>concentrated outside corporate and
    billionaire-owned outlets</strong> — the shape of story that tends to go missing from the biggest feeds.</p>
    ${list.length ? list.map(s => storyCard(s) ).join("") : `<div class="empty">Nothing flagged in the current window.</div>`}`;
}

function renderOutlets() {
  $("#view-outlets").innerHTML = `
    <h2 class="view-title">Outlet files</h2>
    <p class="view-intro">Every outlet we aggregate, with its ownership chain and funding model —
    curated from public records. <strong>No left–right score anywhere.</strong></p>
    <div class="outlet-grid">
      ${Object.values(OUTLETS).map(o => `
        <div class="card outlet-card" style="margin-bottom:0">
          <h3>${ownDot(o.type)}<a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.name)} <span style="font-size:11px;color:var(--muted)">↗</span></a></h3>
          <div class="o-sub">${OWN_TYPES[o.type].label}</div>
          <div class="chain" style="font-size:12px">${o.chain.slice(1).map((n,j)=>`<span class="node">${esc(n)}</span>${j<o.chain.length-2?`<span class="arrow">→</span>`:""}`).join("")}</div>
          <h5>Funding</h5><p>${esc(o.funding)}</p>
          <h5>Other holdings</h5><p>${esc(o.holdings)}</p>
        </div>`).join("")}
    </div>`;
}

function renderAbout() {
  $("#view-about").innerHTML = `
    <h2 class="view-title">How Lede works</h2>
    <p class="view-intro">Built as an answer to the bias-rating model of apps like Ground News —
    see "Ground News and the War on Reality" (Literate Machine, 2026).</p>
    <div class="method-grid">
      <div class="card method-card" style="margin-bottom:0">
        <div class="vs">Live now</div><h3>Ownership, not affiliation</h3>
        <p>No outlet is placed on a political spectrum. We show who owns it, what else the owner holds,
        and how the money flows — and let you judge the coverage yourself.</p>
      </div>
      <div class="card method-card" style="margin-bottom:0">
        <div class="vs">Live now</div><h3>Same story, side by side</h3>
        <p>Articles are clustered by story so you can read how a worker-owned outlet, a nonprofit, and a
        conglomerate each covered the same event — with direct links to every original.</p>
      </div>
      <div class="card method-card" style="margin-bottom:0">
        <div class="vs">Live now</div><h3>Underreported, by ownership</h3>
        <p>Instead of a left-vs-right "blindspot," we flag stories whose coverage is concentrated outside
        corporate and billionaire-owned media.</p>
      </div>
      <div class="card method-card" style="margin-bottom:0">
        <div class="vs">Live with an API key</div><h3>Article-level analysis</h3>
        <p>Each article's headline and summary get an automated read: news vs. opinion classification,
        headline framing flags, and which source types it leans on. Bylines with 3+ analyzed pieces get a
        <b>pattern profile</b>. Deliberately absent: a factuality score — claim verification needs human
        review, and a faked number would be the black-box rating this project exists to replace.</p>
      </div>
    </div>
    <div class="why-box" style="margin-top:16px"><b>Open by design:</b> the feed list, the ownership database,
    and the clustering code are all in this site's repository. If you think an ownership note is wrong,
    open an issue — corrections are part of the product.</div>`;
}

function show(view) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  $("#view-" + view).classList.add("active");
  document.querySelectorAll("nav button").forEach(b =>
    b.classList.toggle("active", b.dataset.v === view || (view === "detail" && b.dataset.v === "feed")));
}

const VIEWS = [["feed","Top stories"],["under","Underreported"],["outlets","Outlet files"],["about","About"]];
$("#nav").innerHTML = VIEWS.map(([id,label]) => `<button data-v="${id}" onclick="show('${id}')">${label}</button>`).join("");

async function boot() {
  try {
    const [own, data, auth] = await Promise.all([
      fetch("ownership.json").then(r => r.json()),
      fetch("stories.json").then(r => r.json()),
      fetch("authors.json").then(r => r.ok ? r.json() : { authors: {} }).catch(() => ({ authors: {} }))
    ]);
    OUTLETS = own.outlets;
    AUTHORS = auth.authors || {};
    STORIES = data.stories || [];
    GENERATED = data.generated;
    $("#gen-badge").textContent = `Updated ${ago(GENERATED)} · ${data.feedsOk}/${data.feedsTotal} feeds`;
    renderFeed(); renderUnder(); renderOutlets(); renderAbout();
    show("feed");
  } catch (e) {
    $("#gen-badge").textContent = "no data";
    $("#view-feed").innerHTML = `<div class="empty">Couldn't load story data.<br><br>
      If you opened this file directly, serve it instead: run <code>python3 -m http.server</code> in this
      folder and open <code>http://localhost:8000</code>. If this is the live site, the first feed run may
      not have happened yet — check the Actions tab.</div>`;
    renderOutletsFallback();
    show("feed");
  }
}
async function renderOutletsFallback() {
  try {
    const own = await fetch("ownership.json").then(r => r.json());
    OUTLETS = own.outlets; renderOutlets(); renderAbout();
  } catch (e) { /* nothing */ }
}
boot();
</script>
</body>
</html>
