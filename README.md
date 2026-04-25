# AU/PR Navigator

Personal PR strategy dashboard for ANZSCO 261111 (ICT Business Analyst) — offshore applicant, 80–85 pts.

Live immigration intelligence in the left sidebar. Click **Open in Claude.ai ↗** to get a personalised strategy — no API key, no proxy, no setup.

---

## Architecture

```
GitHub Actions (daily 9am AEST)
  └─ scripts/run_monitoring.py
       └─ Claude API + web_search → monitoring_data.json
            └─ commits to repo

GitHub Pages
  └─ serves au_pr_strategy.html + monitoring_data.json

Browser
  └─ fetches monitoring_data.json on load
  └─ "Open in Claude.ai ↗" button encodes full prompt → opens claude.ai/new
       └─ no API key, no proxy, no Cloudflare required
```

---

## One-time setup (~5 minutes)

### 1. Fork / push this repo to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/au-pr-navigator.git
git push -u origin main
```

### 2. Enable GitHub Pages

In your repo → **Settings → Pages**:
- Source: `Deploy from a branch`
- Branch: `main` / `/ (root)`

Your dashboard will be live at `https://YOUR_USERNAME.github.io/au-pr-navigator/au_pr_strategy.html`

### 3. Add repo secret for monitoring

In your repo → **Settings → Secrets → Actions → New repository secret**:
- Name: `ANTHROPIC_API_KEY`
- Value: `sk-ant-YOUR_KEY`

The GitHub Actions workflow runs `scripts/run_monitoring.py` daily at 9am AEST and commits updated `monitoring_data.json` to the repo. GitHub Pages picks it up automatically.

Test it immediately: **Actions → Daily Monitoring Update → Run workflow**.

That's it. Open the GitHub Pages URL, check the Live Intel panel, click **Open in Claude.ai ↗**.

---

## Daily monitoring

The GitHub Actions workflow runs every day at 09:00 AEST (free tier — ~2 min/run, ~60 min/month):

1. `scripts/run_monitoring.py` calls Claude with web_search
2. Writes `monitoring_data.json` with up to 5 classified findings
3. Patches the `EMBEDDED` constant in `au_pr_strategy.html` (offline fallback)
4. Commits and pushes if anything changed

To trigger manually: **Actions → Daily Monitoring Update → Run workflow**

**Cost:** Free for public repos (unlimited minutes). Free for private repos up to 2,000 min/month — daily monitoring uses ~60 min/month.

---

## How the strategy works

1. Open the dashboard (GitHub Pages URL)
2. Select your English proficiency (Competent 80 pts / Superior 85 pts)
3. Live Intel panel shows today's classified findings
4. Click **Open in Claude.ai ↗**
5. Your full profile + monitoring intelligence is pre-loaded as the prompt in Claude.ai
6. Claude generates your personalised strategy — no API key required in the browser

---

## Local development

```bash
# Run the dashboard locally with live monitoring data
python3 -m http.server 8000
open http://localhost:8000/au_pr_strategy.html

# Run monitoring manually
ANTHROPIC_API_KEY=sk-ant-... python3 scripts/run_monitoring.py
```

---

## Files

| File | Purpose |
|------|---------|
| `au_pr_strategy.html` | Self-contained dashboard — works offline from file:// |
| `monitoring_data.json` | Latest monitoring output — committed by GitHub Actions daily |
| `scripts/run_monitoring.py` | Daily monitoring script — called by GitHub Actions |
| `.github/workflows/monitor.yml` | Scheduled workflow — runs at 09:00 AEST daily |
