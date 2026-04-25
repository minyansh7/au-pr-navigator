#!/usr/bin/env python3
"""
Daily monitoring script for AU/PR Navigator.
Called by GitHub Actions on schedule. Runs Claude with web_search to
produce an updated monitoring_data.json, then patches the EMBEDDED
constant inside au_pr_strategy.html so the file is always self-contained.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/run_monitoring.py
"""

import anthropic, json, os, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
AEST = timezone(timedelta(hours=10))

SYSTEM = """\
You are a MARA-registered senior Australian migration lawyer and daily \
immigration intelligence analyst. Your task is to monitor the Australian \
immigration landscape for developments relevant to a skilled ICT Business \
Analyst (ANZSCO 261111) offshore applicant pursuing PR via subclass 491, \
190, 189, and 186 TRT.

Run searches across official government sources, professional commentary, \
and community forums. Classify each finding as: critical, important, or monitor.

Mark star=true if ANZSCO 261111 is directly affected by that finding.

After searching, return ONLY a single JSON object — no other text — matching \
this exact schema:

{
  "generated": "<ISO 8601 with +10:00 offset>",
  "date_display": "<DD Mon YYYY>",
  "time_display": "<HH:MM AEST>",
  "has_critical": <true|false>,
  "action_required": "<one sentence or null>",
  "findings": [
    {
      "id": "<kebab-slug>",
      "priority": "critical|important|monitor",
      "star": <true|false>,
      "category": "<e.g. PATH A, PATH B, PATH C, SIGNAL>",
      "title": "<UPPERCASE SHORT TITLE>",
      "body": "<2-3 sentences. Specific: subclass numbers, dates, figures.>",
      "url": "<primary official source URL>",
      "deadline_iso": "<ISO 8601 or null>"
    }
  ]
}

Maximum 5 findings. If all findings are no-action, return has_critical=false \
and an empty findings array.\
"""

USER = """\
Today is {date}. Run the full daily monitoring sequence:

1. Check immi.homeaffairs.gov.au for new 189/190/491 invitation round data
2. Check liveinmelbourne.vic.gov.au for new Victoria rounds or ROI closure notices
3. Search: "Victoria 190 invitation round {month_year}"
4. Search: "Victoria 491 invitation round {month_year}"
5. Search: "SkillSelect 189 invitation round {month_year}"
6. Search: "Australia skilled migration occupation list change 2026"
7. Search: "ANZSCO 261111 ICT Business Analyst {year}"
8. Search: "Australia 482 Skills in Demand visa changes {year}"
9. Search: "Australia 186 TRT employer nomination {year}"
10. Search: "Australia TSMIT threshold {year}"
11. Check minister.homeaffairs.gov.au for media releases in last 24h

Return the JSON object only.\
"""


def run():
    now = datetime.now(AEST)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = USER.format(
        date=now.strftime("%-d %B %Y"),
        month_year=now.strftime("%B %Y"),
        year=now.year,
    )

    print(f"Running monitoring for {now.strftime('%d %b %Y %H:%M AEST')} …")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 20}],
    )

    # Extract JSON from response text blocks
    text = "".join(b.text for b in response.content if hasattr(b, "text"))
    match = re.search(r"\{[\s\S]+\}", text)
    if not match:
        print("ERROR: no JSON found in response", file=sys.stderr)
        print(text[:500], file=sys.stderr)
        sys.exit(1)

    data = json.loads(match.group())
    n = len(data.get("findings", []))
    print(f"  {n} finding(s), has_critical={data.get('has_critical')}")

    # Write monitoring_data.json
    out = ROOT / "monitoring_data.json"
    out.write_text(json.dumps(data, indent=2))
    print(f"  Wrote {out}")

    # Patch EMBEDDED constant in HTML so file stays self-contained offline
    html_path = ROOT / "au_pr_strategy.html"
    html = html_path.read_text()
    patched = re.sub(
        r"const EMBEDDED = \{.*?\};",
        f"const EMBEDDED = {json.dumps(data, separators=(',', ':'))};",
        html,
        flags=re.DOTALL,
    )
    if patched != html:
        html_path.write_text(patched)
        print(f"  Patched EMBEDDED in {html_path.name}")

    return data


if __name__ == "__main__":
    run()
