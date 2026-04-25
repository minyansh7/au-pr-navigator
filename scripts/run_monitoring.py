#!/usr/bin/env python3
"""
Daily monitoring for AU/PR Navigator — zero API key edition.
Fetches official government sources and applies date-aware rule classification.
No external API keys or dependencies beyond the Python stdlib.

Usage:
  python3 scripts/run_monitoring.py
"""

import json, re, sys, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
AEST = timezone(timedelta(hours=10))
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AU-PR-Navigator/1.0; +https://github.com)"}


def fetch(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN fetch {url}: {e}", file=sys.stderr)
        return ""


def plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def run():
    now = datetime.now(AEST)
    findings = []
    print(f"Running monitoring for {now.strftime('%d %b %Y %H:%M AEST')} …")

    # ── 1. Victoria 190/491 ROI deadline ──────────────────────────────────
    vic_deadline = datetime(2026, 4, 28, 16, 0, 0, tzinfo=AEST)
    if now < vic_deadline:
        days_left = (vic_deadline - now).days
        findings.append({
            "id": "vic-roi-closure",
            "priority": "critical" if days_left <= 7 else "important",
            "star": True,
            "category": "PATH A",
            "title": f"VICTORIA ROI CLOSES 28 APRIL 2026 — {days_left}d LEFT",
            "body": (
                "Victoria's 2025-26 state-nominated skilled visa program closes to ALL new "
                "Registrations of Interest at 4:00 PM AEST on Tuesday 28 April. "
                "The 3,400-place allocation (subclasses 190 & 491, down 32% on 2024-25) "
                "is near exhaustion. ICT occupations featured strongly in 2025-26 rounds."
            ),
            "url": "https://liveinmelbourne.vic.gov.au/news-events/news/2026/update-on-victorias-skilled-visa-nomination-program-2025-26",
            "deadline_iso": vic_deadline.isoformat(),
        })

    # ── 2. SID overhaul (gazetted 18 Apr 2026, show for 12 months) ───────
    if now < datetime(2027, 4, 18, tzinfo=AEST):
        findings.append({
            "id": "sid-overhaul",
            "priority": "important",
            "star": True,
            "category": "PATH B",
            "title": "482 SID VISA OVERHAUL ENACTED 18 APR 2026",
            "body": (
                "Regulations gazetted 18 April 2026 replace subclass 482 TSS with "
                "three-stream Skills in Demand (SID): Specialist Skills (SSIT $141,210+), "
                "Core Skills (new CSOL), Essential Skills (labour agreement). "
                "186 TRT qualifying period confirmed at 2 years on SID. "
                "Job mobility extended from 60 to 180 days."
            ),
            "url": "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/skills-in-demand-visa-subclass-482",
            "deadline_iso": None,
        })

    # ── 3. CSIT indexation from 1 July 2026 ──────────────────────────────
    csit_deadline = datetime(2026, 7, 1, tzinfo=AEST)
    if now < csit_deadline:
        findings.append({
            "id": "csit-indexation",
            "priority": "important",
            "star": False,
            "category": "PATH B",
            "title": "CSIT RISES TO $79,499 FROM 1 JULY 2026",
            "body": (
                "Core Skills Income Threshold auto-indexes to $79,499 "
                "(SSIT to $146,717) from 1 July 2026 under AWOTE indexation (Reg 5.42A). "
                "Legacy TSMIT ($76,515) requires separate ministerial instrument. "
                "Any 186 TRT nomination lodged on or after 1 July 2026 must meet the new floor."
            ),
            "url": "https://workingin.com.au/news/new-income-thresholds-from-1-july-2026/",
            "deadline_iso": csit_deadline.isoformat(),
        })

    # ── 4. SkillSelect 189 — check if a Q4 round has been issued ─────────
    ss_html = fetch(
        "https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/invitation-rounds"
    )
    q4_issued = bool(ss_html and any(
        k in ss_html for k in ["April 2026", "May 2026", "June 2026"]
    ))
    findings.append({
        "id": "189-q4-issued" if q4_issued else "189-q4-pending",
        "priority": "monitor",
        "star": True,
        "category": "PATH C",
        "title": "189 Q4 ROUND ISSUED — CHECK EOI" if q4_issued else "189 Q4 ROUND IMMINENT — NO DRAW ISSUED YET",
        "body": (
            "A subclass 189 invitation round has been issued for Q4 2026. "
            "Check your SkillSelect EOI status immediately. ANZSCO 261111 typically "
            "requires 85–90+ pts under Ministerial Direction 105."
        ) if q4_issued else (
            f"No subclass 189 invitation issued for Q4 (Apr–Jun 2026) as at "
            f"{now.strftime('%-d %b')}. Q1 round (13 Nov 2025) issued ~10,000 invitations. "
            "ANZSCO 261111 typically requires 85–90+ pts. Rounds open without notice."
        ),
        "url": "https://immi.homeaffairs.gov.au/visas/working-in-australia/skillselect/invitation-rounds",
        "deadline_iso": None,
    })

    # ── 5. Live in Melbourne — look for new post-April notices ────────────
    vim_html = fetch("https://liveinmelbourne.vic.gov.au/news-events/news")
    new_vic_notice = bool(vim_html and re.search(
        r"(invitation|round|nominations?)\s+\w+\s+(May|Jun[e]?|Jul[y]?|Aug)\s+2026",
        plain(vim_html), re.I,
    ))
    if new_vic_notice:
        findings.append({
            "id": "vic-new-notice",
            "priority": "important",
            "star": True,
            "category": "PATH A",
            "title": "NEW VICTORIA NOTICE DETECTED",
            "body": (
                "A new invitation round or nomination notice has appeared on the Live in Melbourne "
                "news page for a month after April 2026. Check the source for eligibility criteria, "
                "occupation lists, and application deadlines."
            ),
            "url": "https://liveinmelbourne.vic.gov.au/news-events/news",
            "deadline_iso": None,
        })
    else:
        findings.append({
            "id": "nsw-quota-signal",
            "priority": "monitor",
            "star": False,
            "category": "SIGNAL",
            "title": "NSW APRIL ROUNDS CONSUMING NATIONAL QUOTA",
            "body": (
                "NSW 190 round completed w/c 13 April; 491 Pathway 2 round scheduled w/c 27 April. "
                "Multi-state drawdown of the 20,350-place program year signals accelerating quota "
                "consumption — reinforces urgency of Victoria 28 Apr deadline."
            ),
            "url": "https://www.inclusivemigration.com.au/news/nsw-will-be-conducting-upcoming-subclass-190-amp-491-invitation-rounds-in-april-2026",
            "deadline_iso": None,
        })

    findings = findings[:5]
    has_critical = any(f["priority"] == "critical" for f in findings)

    data = {
        "generated": now.isoformat(),
        "date_display": now.strftime("%-d %b %Y"),
        "time_display": now.strftime("%H:%M AEST"),
        "has_critical": has_critical,
        "action_required": (
            "Verify your Victoria ROI is submitted and active in the Live in Melbourne "
            "portal before 4:00 PM AEST Tuesday 28 April 2026."
        ) if has_critical else None,
        "findings": findings,
    }

    print(f"  {len(findings)} finding(s), has_critical={has_critical}")

    # Write monitoring_data.json
    (ROOT / "monitoring_data.json").write_text(json.dumps(data, indent=2))
    print(f"  Wrote monitoring_data.json")

    # Patch EMBEDDED constant in HTML for offline fallback
    html_path = ROOT / "au_pr_strategy.html"
    html = html_path.read_text()
    patched = re.sub(
        r"const EMBEDDED = \{.*?\};",
        lambda _: f"const EMBEDDED = {json.dumps(data, separators=(',', ':'), ensure_ascii=True)};",
        html,
        flags=re.DOTALL,
    )
    if patched != html:
        html_path.write_text(patched)
        print(f"  Patched EMBEDDED in {html_path.name}")

    return data


if __name__ == "__main__":
    run()
