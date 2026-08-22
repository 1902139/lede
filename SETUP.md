# Setting up Lede — complete walkthrough

Everything here is free except Stage 2 (a few cents to ~$2/month). No servers,
no command line required. Budget about 20 minutes.

You'll do this in three parts:

- **Part A** — get the site online (~10 min, free) → you have a link to share
- **Part B** — turn on the hourly auto-updater (~3 min, free)
- **Part C** — turn on Stage 2 article analysis (~7 min, small cost) — optional,
  and the site works fine without it

---

# Part A — Get the site online

### A1. Make a GitHub account

Go to **github.com** and click **Sign up**. Free plan is all you need. Verify
your email — GitHub won't let you create repositories until you do.

### A2. Create the repository

1. Once logged in, click the **+** in the top-right corner → **New repository**.
2. **Repository name:** `lede` (lowercase; this becomes part of your web address)
3. **Public** — required, because free GitHub Pages hosting only works on public
   repos. This means anyone can read the code; it does *not* mean anyone can
   change it.
4. Leave every checkbox unticked ("Add a README", ".gitignore", "license" — all off).
5. Click **Create repository**.

You'll land on a mostly empty page with setup instructions. Ignore all of it.

### A3. Upload the files

1. Unzip `lede-site.zip` on your computer. You should see: `index.html`,
   `README.md`, `SETUP.md`, and the `.github` folder (all other files sit at the top level).
2. On your new repo page, click the link **uploading an existing file**
   (it's in the middle of the setup instructions). If you don't see it, go to
   `https://github.com/YOUR-USERNAME/lede/upload/main`
3. Open the unzipped `lede-site` folder, select **all** of its contents
   (Ctrl+A / Cmd+A) and drag them into the browser window.
4. Wait for the file list to finish loading, then scroll down and click
   **Commit changes**.

**Important — check for the hidden folder.** Look at your repo's file list.
Do you see a folder named `.github`? Folders starting with a dot are hidden by
default on Mac and Linux, and often don't get dragged in.

If `.github` is **missing**, create it by hand:

1. Click **Add file** → **Create new file**
2. In the filename box, type exactly: `.github/workflows/update.yml`
   (typing the slashes automatically creates the folders)
3. Open `update.yml` from the unzipped folder in any text editor, copy
   everything, and paste it into the big box on GitHub.
4. Click **Commit changes**.

### A4. Turn on hosting

1. In your repo, click **Settings** (top row, right side — gear icon).
2. In the left sidebar, click **Pages**.
3. Under "Build and deployment" → **Source**, choose **Deploy from a branch**.
4. Under **Branch**, pick `main`, keep the folder as `/ (root)`, click **Save**.
5. Wait about a minute, then refresh the page. A green box appears at the top
   with your address:

   **`https://YOUR-USERNAME.github.io/lede/`**

That's your link. Open it — you'll see the site with outlet files working, and
a message that story data hasn't been fetched yet. Part B fixes that.

---

# Part B — Turn on the hourly updater

The site needs a robot to fetch news for it. That's the GitHub Action.

### B1. Give the robot permission to save files

1. **Settings** → in the left sidebar, **Actions** → **General**
2. Scroll all the way down to **Workflow permissions**
3. Select **Read and write permissions** (the default is read-only, which
   silently blocks the updater from saving results)
4. Click **Save**

### B2. Run it once by hand

1. Click the **Actions** tab (top row of your repo).
2. If you see a "Workflows aren't being run on this forked repository" or a
   green "I understand my workflows, go ahead and enable them" button, click it.
3. In the left sidebar, click **Update stories**.
4. On the right, click **Run workflow** → **Run workflow** (green button).
5. Wait ~1 minute, refresh. You'll see a run appear with a yellow dot (running),
   then green check (worked) or red X (failed).

### B3. Check the result

Click the run, then click the `fetch` job to see the log. Look for a line like:

```
feeds ok: 27/34, articles in window: 412
wrote data/stories.json with 38 stories
```

**Some feeds failing is normal and expected.** Outlets change their RSS URLs
without warning. As long as most work, you're fine. Failing ones are listed in
the log as `FAILED: <url>` — to fix one, find that URL in `ownership.json`
and correct or remove it (edit files directly on GitHub: click the file, then
the pencil icon).

Now open your site link. Real stories, real ownership bars, real links.

From here it updates itself every hour, forever, free. You can stop reading if
you don't want Stage 2.

---

# Part C — Stage 2: article analysis (optional)

This adds automated headline framing flags, better news/opinion classification,
source-type detection, and author pattern profiles. It uses the Claude API.

**What it costs:** roughly $0.10–$2.00 per month at this scale. Each article is
analyzed exactly once (results are cached forever), and only headline +
summary text is sent — never full articles. Anthropic requires a minimum
prepaid credit purchase, typically $5, which will last you a long time.

**What it deliberately does NOT do:** assign factuality scores. Verifying claims
against primary sources credibly requires human review — an automated
"factuality percentage" would be exactly the black-box rating this project
exists to replace. The author files show observable patterns instead.

### C1. Get an API key

1. Go to **console.anthropic.com** and sign up (separate from your Claude
   subscription — API usage is billed separately).
2. Click **Billing** in the sidebar → add a payment method → buy credits
   (the $5 minimum is plenty).
3. Click **API keys** in the sidebar → **Create key** → name it `lede` →
   **Create**.
4. **Copy the key immediately** — it starts with `sk-ant-` and is shown only
   once. If you lose it, just delete it and make a new one.

### C2. Give the key to your repo (safely)

Never paste the key into a file. GitHub has an encrypted vault for this.

1. In your repo: **Settings** → left sidebar **Secrets and variables** →
   **Actions**
2. Click **New repository secret**
3. **Name:** `ANTHROPIC_API_KEY` — exactly this, all caps with underscores
4. **Secret:** paste your key
5. Click **Add secret**

The key is now write-only — even you can't read it back, and it never appears
in logs. The workflow already knows to look for it.

### C3. Run it

**Actions** → **Update stories** → **Run workflow**. Check the log for:

```
analyze: 47 new articles to analyze
analyze: done — cache 47, authors 12, failed 0
```

Refresh your site. Articles now show framing flags and source chips, and
bylines with 3+ tracked pieces become clickable pattern profiles.

If you skip Part C entirely, the analysis step prints "skipping Stage 2" and
everything else works normally.

---

# Sharing it

Just send the link: `https://YOUR-USERNAME.github.io/lede/`

It works on phones, needs no account, and nobody you share it with can break
anything. If you want a custom domain later (like `lede.news`), buy one from
any registrar (~$12/year) and point it at GitHub Pages under Settings → Pages
→ Custom domain.

---

# Part D — Fact-check ratings for people in the news (optional, free)

This adds a panel to stories showing what fact-checking organisations have found
about **the public figures quoted in them** — politicians, officials, campaign
groups. It does not rate journalists: fact-checkers barely check reporters, so
any such score would rest on a sample of one or two.

Data comes from Google's **Fact Check Tools API**, which aggregates the
ClaimReview data PolitiFact, FactCheck.org, Snopes, AFP and others publish
specifically for machines to read. It is **free** and needs no billing account.

### D1. Get a Google API key

1. Go to **console.cloud.google.com** and sign in with any Google account.
2. Click the project dropdown at the top → **New Project** → name it `lede` →
   **Create**. Wait a few seconds and make sure the new project is selected.
3. In the search bar at the top, type **Fact Check Tools API** and open it.
4. Click **Enable**.
5. In the left sidebar go to **APIs & Services → Credentials**.
6. Click **+ Create credentials → API key**. Copy the key it shows you.
7. Optional but sensible: click **Edit API key**, and under "API restrictions"
   choose **Restrict key** → tick **Fact Check Tools API** → Save. That way the
   key can do nothing else.

### D2. Add it to your repo

1. Your repo → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `GOOGLE_FACTCHECK_KEY` — exactly this
4. Secret: paste the key → **Add secret**

### D3. Run it

**Actions → Update stories → Run workflow.** Look for a line like:

```
factchecks: 4210 claims fetched
factchecks: 186 people with 5+ checks -> factchecks.json
```

Then open a political story on your site. If anyone in it has been fact-checked,
you'll see a panel with their rating breakdown and links to the original checks.

**Things worth knowing:**

- The script refreshes about **once a day**, not hourly, to stay inside the free
  quota. It skips itself if the data is under 20 hours old.
- Only people with **5 or more checks** appear. Below that a percentage is noise.
- Names are matched automatically against story text. It requires a full name, or
  a surname unique among fact-checked people, and ignores organisation-shaped
  names — but it can still occasionally be wrong.
- Without the key the step prints "skipping" and everything else works normally.

---

# Troubleshooting

**Site shows "Couldn't load story data"**
The fetcher hasn't run yet, or it failed. Do Part B. If it ran green, check
that `stories.json` exists in your repo and isn't the placeholder.

**Action fails with "Permission denied" or "403"**
You missed step B1. Settings → Actions → General → Workflow permissions →
Read and write.

**Action is green but the site doesn't change**
GitHub Pages caches for a minute or two. Hard-refresh (Ctrl+Shift+R /
Cmd+Shift+R). Also confirm Pages is set to branch `main`, folder `/ (root)`.

**"Update stories" doesn't appear in the Actions tab**
The `.github/workflows/update.yml` file didn't upload. See the hidden-folder
note at the end of step A3.

**Lots of feeds failing**
Normal for a few. If nearly all fail, the outlets may be blocking GitHub's
servers — tell me and I'll swap in alternate feed URLs.

**Stories look wrongly grouped together**
Clustering matches headline words and is imperfect by nature. In
`fetch_news.py`, raise `JACCARD_JOIN` (0.20 → 0.28) to group less
eagerly, or lower it to group more.

**Analysis step says "ANTHROPIC_API_KEY not set" even though I added it**
The secret name must be exactly `ANTHROPIC_API_KEY`. Check for typos, extra
spaces, or that you added it as a *repository* secret (not an environment or
organization one).

---

# Running it on your own computer instead (optional)

Only if you'd rather test locally before publishing:

```bash
pip install feedparser
python fetch_news.py         # fetch real feeds
python analyze.py --mock     # fake analysis, no API key needed
python -m http.server                # then open http://localhost:8000
```

Double-clicking `index.html` will *not* work — browsers block local data
loading for security. The `http.server` line above is the workaround.
