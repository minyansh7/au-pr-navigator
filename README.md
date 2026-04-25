# AU/PR Navigator

Personal PR strategy dashboard for ANZSCO 261111 (ICT Business Analyst) — offshore applicant, 80–85 pts.

Live immigration intelligence in the left sidebar. Click **Run Strategy** for a personalised Claude-generated strategy based on today's monitoring data.

---

## Architecture

```
GitHub Actions (daily 9am AEST)
  └─ scripts/run_monitoring.py
       └─ Claude API + web_search → monitoring_data.json
            └─ commits to repo

GitHub Pages
  └─ serves au_pr_strategy.html + monitoring_data.json

Cloudflare Worker (au-pr-monitor-proxy)
  └─ proxies POST /messages → Anthropic API
       └─ ANTHROPIC_API_KEY lives in Worker secret (never in browser)
```

---

## One-time setup (~15 minutes)

### 1. Fork / push this repo to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/au-pr-navigator.git
git push -u origin feat/live-monitoring-integration
# merge to main, then:
git push origin main
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

### 4. Deploy the Cloudflare Worker

```bash
# Install Wrangler (one-time)
npm install -g wrangler
wrangler login

# Deploy
cd worker
wrangler deploy

# Set your API key as a Worker secret (never stored in code)
wrangler secret put ANTHROPIC_API_KEY
# paste your sk-ant-... key when prompted
```

Your Worker URL will be: `https://au-pr-monitor-proxy.YOUR_NAME.workers.dev`

### 5. Connect the dashboard to the Worker

Open your GitHub Pages URL, click **⚙ API Key**, enter:
- **Proxy URL**: `https://au-pr-monitor-proxy.YOUR_NAME.workers.dev`
- **API Key**: leave blank (key is in the Worker secret)

Click **Save**. Click **Run Strategy**. Done.

---

## Daily monitoring

The GitHub Actions workflow runs every day at 09:00 AEST:

1. `scripts/run_monitoring.py` calls Claude with web_search
2. Writes `monitoring_data.json` with up to 5 classified findings
3. Patches the `EMBEDDED` constant in `au_pr_strategy.html` (offline fallback)
4. Commits and pushes if anything changed

To trigger manually: **Actions → Daily Monitoring Update → Run workflow**

---

## Local development

```bash
# Run the dashboard locally with live monitoring data
python3 proxy.py --key sk-ant-YOUR_KEY   # terminal 1
python3 -m http.server 8000              # terminal 2
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
| `worker/index.js` | Cloudflare Worker (23 lines) — CORS proxy to Anthropic API |
| `worker/wrangler.toml` | Cloudflare deployment config |
| `scripts/run_monitoring.py` | Daily monitoring script — called by GitHub Actions |
| `.github/workflows/monitor.yml` | Scheduled workflow — runs at 09:00 AEST daily |
| `proxy.py` | Local CORS proxy — alternative to Cloudflare for local use |
