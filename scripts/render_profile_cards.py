
#!/usr/bin/env python3
"""Generate animated white-theme SVG cards for Akashh28."""
from __future__ import annotations

import argparse
import base64
import calendar
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "contributions.json"
OUT = ROOT / "cards"

USERNAME = "Akashh28"
STATIC = os.getenv("STATIC") == "1"
PORTRAIT_URL = os.getenv("PROFILE_PORTRAIT_URL", "").strip()

# WHITE MINIMAL THEME
BG = "#FFFFFF"
PANEL = "#FFFFFF"
PANEL2 = "#F8FAFC"

LINE = "#E5E7EB"
TEXT = "#111827"
MUTED = "#64748B"

PURPLE = "#111827"
BLUE = "#4B5563"
GREEN = "#9CA3AF"

FONT_URLS = {
    "dm": "https://raw.githubusercontent.com/google/fonts/main/ofl/dmsans/DMSans[opsz,wght].ttf",
    "space": "https://raw.githubusercontent.com/google/fonts/main/ofl/spacegrotesk/SpaceGrotesk[wght].ttf",
}

TILES = [
    (
        "01",
        "BUILD",
        "Python projects & practical builds",
        "https://github.com/Akashh28?tab=repositories",
        PURPLE,
    ),
    (
        "02",
        "BRAND",
        "My portfolio & developer identity",
        "https://akashh28.github.io/portfolioo/",
        BLUE,
    ),
    (
        "03",
        "LEARN",
        "AI/ML · Python · Information Science",
        "https://github.com/Akashh28",
        GREEN,
    ),
]

REPOS = [
    {
        "name": "CodeAlpha_BasicChatbot",
        "desc": "A beginner-friendly, rule-based Python chatbot built for the CodeAlpha internship.",
        "lang": "Python",
        "url": "https://github.com/Akashh28/CodeAlpha_BasicChatbot",
    },
    {
        "name": "simplecalci",
        "desc": "A command-line calculator for basic arithmetic, including division-by-zero handling.",
        "lang": "Python",
        "url": "https://github.com/Akashh28/simplecalci",
    },
    {
        "name": "portfolioo",
        "desc": "My personal portfolio: a clean, minimal space for my work, skills and experiments.",
        "lang": "HTML · CSS · JavaScript",
        "url": "https://github.com/Akashh28/portfolioo",
    },
]


def download(url, destination):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Akashh28-profile-cards/1.0"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        destination.write_bytes(response.read())


def refresh_contributions():
    token = os.getenv("PROFILE_STATS_TOKEN") or os.getenv("GH_TOKEN")

    if not token:
        raise SystemExit(
            "Set PROFILE_STATS_TOKEN to a GitHub token with read:user scope."
        )

    today = date.today()
    start = today - timedelta(days=365)

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
                weekday
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "login": USERNAME,
        "from": datetime.combine(
            start, datetime.min.time(), timezone.utc
        ).isoformat().replace("+00:00", "Z"),
        "to": datetime.combine(
            today, datetime.max.time(), timezone.utc
        ).isoformat().replace("+00:00", "Z"),
    }

    body = json.dumps({
        "query": query,
        "variables": variables,
    }).encode()

    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Akashh28-profile-cards/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=45) as response:
        result = json.loads(response.read())

    if result.get("errors"):
        raise SystemExit(
            "GitHub GraphQL error: " + json.dumps(result["errors"])
        )

    cal = result["data"]["user"]["contributionsCollection"][
        "contributionCalendar"
    ]

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    DATA_FILE.write_text(
        json.dumps(
            {
                "username": USERNAME,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_contributions": cal["totalContributions"],
                "weeks": cal["weeks"],
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("Contribution JSON refreshed.")


def load_days():
    if not DATA_FILE.exists():
        raise SystemExit(
            f"Missing {DATA_FILE}; run with --refresh-data."
        )

    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    days = {}

    for week in raw.get("weeks", []):
        for item in week.get("contributionDays", []):
            try:
                days[date.fromisoformat(item["date"])] = int(
                    item.get("contributionCount", 0)
                )
            except (KeyError, TypeError, ValueError):
                pass

    for item in raw.get("days", []):
        try:
            days[date.fromisoformat(item["date"])] = int(
                item.get("count", 0)
            )
        except (KeyError, TypeError, ValueError):
            pass

    return days


def calculate_metrics(days):
    today = date.today()

    dates = [
        today - timedelta(days=i)
        for i in range(364, -1, -1)
    ]

    counts = {d: days.get(d, 0) for d in dates}
    active = sum(v > 0 for v in counts.values())

    cursor = today if counts.get(today, 0) > 0 else today - timedelta(days=1)
    streak = 0

    while counts.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)

    longest = run = 0
    previous = None

    for d in dates:
        if counts[d] > 0:
            run = run + 1 if previous == d - timedelta(days=1) else 1
            longest = max(longest, run)
        else:
            run = 0

        previous = d

    months = []

    for offset in range(11, -1, -1):
        year, month = today.year, today.month - offset

        while month < 1:
            month += 12
            year -= 1

        months.append({
            "label": calendar.month_abbr[month],
            "total": sum(
                v for d, v in counts.items()
                if d.year == year and d.month == month
            ),
        })

    busiest = max(counts, key=lambda d: (counts[d], d))

    return {
        "days": counts,
        "active_days": active,
        "streak": streak,
        "longest_streak": longest,
        "busiest_day": busiest,
        "busiest_count": counts[busiest],
        "months": months,
        "total": sum(counts.values()),
    }


def subset_fonts(temp_dir):
    exe = shutil.which("pyftsubset")

    if not exe:
        raise SystemExit(
            "Install fonttools: python -m pip install fonttools"
        )

    chars = (
        "K Akash Akashh28 Information Science student Aspiring AI ML Engineer "
        "Learning building practical software About me Projects Let's connect "
        "GitHub contributions streak active days busiest day Python HTML CSS "
        "JavaScript CodeAlpha Basic Chatbot simplecalci portfolioo Current "
        "streak Longest streak Last 12 months Total contributions January "
        "February March April May June July August September October November "
        "December 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
        ".,:;!?@#&()[]+-_/·—'’↗★"
    )

    text_file = temp_dir / "subset.txt"
    text_file.write_text(chars, encoding="utf-8")

    result = {}

    for family, url in FONT_URLS.items():
        source = temp_dir / (family + ".ttf")
        output = temp_dir / (family + ".woff")

        download(url, source)

        subprocess.run(
            [
                exe,
                str(source),
                f"--text-file={text_file}",
                "--flavor=woff",
                f"--output-file={output}",
                "--layout-features=*",
                "--name-IDs=*",
                "--name-languages=*",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        result[family] = base64.b64encode(
            output.read_bytes()
        ).decode("ascii")

    return result


def font_css(fonts):
    return (
        "@font-face{font-family:'DM Sans';"
        "src:url(data:font/woff;base64,"
        + fonts["dm"]
        + ") format('woff');font-weight:100 900;}"
        "@font-face{font-family:'Space Grotesk';"
        "src:url(data:font/woff;base64,"
        + fonts["space"]
        + ") format('woff');font-weight:100 900;}"
    )


def svg_start(w, h, title, fonts, delay, animated):
    motion = ""

    if animated:
        motion = (
            f".enter{{animation:rise .9s cubic-bezier(.2,.75,.25,1) both;"
            f"animation-delay:{delay:.2f}s}}"
            "@keyframes rise{from{opacity:0;transform:translateY(22px)}"
            "to{opacity:1;transform:translateY(0)}}"
            "@media(prefers-reduced-motion:reduce){"
            ".enter{animation:none!important;opacity:1!important;"
            "transform:none!important}animate,animateTransform{display:none!important}}"
        )

    group = ' class="enter"' if animated else ""

    smil = (
        '<animate attributeName="opacity" values=".55;1;.55" '
        'dur="4.8s" repeatCount="indefinite"/>'
        if animated else ""
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
width="{w}" height="{h}" viewBox="0 0 {w} {h}"
role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>{font_css(fonts)}
text{{font-family:'DM Sans',sans-serif}}
.heading{{font-family:'Space Grotesk',sans-serif}}
{motion}</style>
<defs>
 <linearGradient id="surface" x1="0" y1="0" x2="1" y2="1">
  <stop stop-color="{PANEL}"/>
  <stop offset="1" stop-color="{PANEL2}"/>
 </linearGradient>
 <linearGradient id="accent">
  <stop stop-color="{PURPLE}"/>
  <stop offset="1" stop-color="{BLUE}"/>
 </linearGradient>
 <clipPath id="portrait-clip">
  <circle cx="1010" cy="126" r="42"/>
 </clipPath>
</defs>
<rect x="1" y="1" width="{w-2}" height="{h-2}"
rx="24" fill="url(#surface)" stroke="{LINE}" stroke-width="1.5"/>
<g{group}>
 <rect x="1" y="1" width="5" height="{h-2}"
 rx="2" fill="url(#accent)"/>
 <circle cx="{w-48}" cy="38" r="3" fill="{PURPLE}">
  {smil}
 </circle>
"""


def svg_end():
    return "</g></svg>\n"


def txt(x, y, value, size, color=TEXT, weight=400, cls=""):
    c = f' class="{cls}"' if cls else ""

    return (
        f'<text x="{x}" y="{y}" font-size="{size}" '
        f'fill="{color}" font-weight="{weight}"{c}>'
        f'{escape(str(value))}</text>'
    )


def save(name, content):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(content, encoding="utf-8")


def render_hero(fonts, delay, animated):
    s = svg_start(
        1200, 250,
        "K Akash — aspiring AI/ML engineer",
        fonts, delay, animated
    )

    s += txt(48, 56, "HELLO, I'M", 13, PURPLE, 700)
    s += txt(48, 132, "K Akash", 58, TEXT, 700, "heading")

    s += txt(
        50, 174,
        "Information Science student  ·  Aspiring AI/ML Engineer",
        21, MUTED, 600
    )

    s += txt(
        50, 211,
        "Learning AI/ML by building practical software, one project at a time.",
        16
    )

    s += (
        '<rect x="900" y="70" width="220" height="112" '
        'rx="22" fill="#F3F4F6" stroke="#D1D5DB"/>'
    )

    if PORTRAIT_URL:
        s += (
            f'<image href="{escape(PORTRAIT_URL)}" '
            'x="968" y="84" width="84" height="84" '
            'preserveAspectRatio="xMidYMid slice" '
            'clip-path="url(#portrait-clip)"/>'
        )
    else:
        s += (
            '<circle cx="1010" cy="126" r="43" '
            'fill="url(#accent)" opacity=".12"/>'
        )

        s += txt(
            1010, 145, "AK", 43, TEXT, 700, "heading"
        ).replace(
            'x="1010"',
            'x="1010" text-anchor="middle"'
        )

    s += txt(
        1010, 207, "BUILD · LEARN · REPEAT",
        11, MUTED, 700
    ).replace(
        'x="1010"',
        'x="1010" text-anchor="middle"'
    )

    save("hero.svg", s + svg_end())


def render_tile(i, item, fonts, delay, animated):
    number, title, subtitle, url, color = item

    s = svg_start(
        380, 118, title, fonts, delay, animated
    )

    s += (
        f'<circle cx="46" cy="58" r="23" '
        f'fill="{color}" fill-opacity=".08" '
        f'stroke="{color}" stroke-opacity=".45"/>'
    )

    s += txt(
        46, 63, number, 13, color, 700
    ).replace(
        'x="46"',
        'x="46" text-anchor="middle"'
    )

    s += txt(88, 48, title, 17, TEXT, 700, "heading")
    s += txt(88, 77, subtitle, 12, MUTED)
    s += txt(330, 70, "↗", 22, color, 700)

    save(f"tile-{i}.svg", s + svg_end())


def render_activity(m, fonts, delay, animated):
    s = svg_start(
        1200, 300,
        "Monthly contributions, streak and active days",
        fonts, delay, animated
    )

    s += txt(
        42, 48, "CONTRIBUTION ACTIVITY",
        13, PURPLE, 700
    )

    s += txt(
        42, 82, "Consistency over time",
        25, TEXT, 700, "heading"
    )

    stats = [
        ("CURRENT STREAK", f'{m["streak"]} days'),
        ("LONGEST STREAK", f'{m["longest_streak"]} days'),
        ("ACTIVE DAYS", f'{m["active_days"]} / 365'),
        (
            "BUSIEST DAY",
            f'{m["busiest_day"].strftime("%d %b")} · {m["busiest_count"]}'
        ),
    ]

    for i, (title, value) in enumerate(stats):
        x = 42 + i * 280

        s += (
            f'<rect x="{x}" y="105" width="258" height="66" '
            f'rx="13" fill="{BG}" stroke="{LINE}"/>'
        )

        s += txt(x + 15, 129, title, 10, MUTED, 700)
        s += txt(x + 15, 155, value, 19, TEXT, 700, "heading")

    chart_x, chart_y, chart_w, chart_h, gap = 48, 205, 1100, 62, 10

    max_value = max(
        [v["total"] for v in m["months"]] + [1]
    )

    bar_w = (chart_w - gap * 11) / 12

    for i, month in enumerate(m["months"]):
        x = chart_x + i * (bar_w + gap)
        h = max(3, chart_h * month["total"] / max_value)

        s += (
            f'<rect x="{x:.1f}" '
            f'y="{chart_y + chart_h - h:.1f}" '
            f'width="{bar_w:.1f}" height="{h:.1f}" '
            f'rx="5" fill="url(#accent)"/>'
        )

        s += txt(
            x + bar_w / 2, 287, month["label"],
            10, MUTED, 500
        ).replace(
            f'x="{x + bar_w / 2:.1f}"',
            f'x="{x + bar_w / 2:.1f}" text-anchor="middle"'
        )

    save("activity.svg", s + svg_end())


def render_repo(repo, index, fonts, delay, animated):
    s = svg_start(
        380, 220, repo["name"], fonts, delay, animated
    )

    s += txt(24, 32, f"PROJECT / 0{index}", 10, PURPLE, 700)
    s += txt(24, 70, repo["name"], 19, TEXT, 700, "heading")

    words = repo["desc"].split()
    lines = []
    line = ""

    for word in words:
        candidate = f"{line} {word}".strip()

        if len(candidate) > 38:
            lines.append(line)
            line = word
        else:
            line = candidate

    if line:
        lines.append(line)

    for i, description in enumerate(lines[:3]):
        s += txt(
            24, 108 + i * 19,
            description, 11, MUTED
        )

    s += (
        f'<rect x="24" y="177" width="150" height="25" '
        f'rx="12" fill="{PURPLE}" fill-opacity=".07" '
        f'stroke="{LINE}"/>'
    )

    s += txt(
        99, 194, repo["lang"], 10, PURPLE, 700
    ).replace(
        'x="99"',
        'x="99" text-anchor="middle"'
    )

    button_text = txt(
        310, 194, "VIEW ↗", 10, "#FFFFFF", 700
    ).replace(
        'x="310"',
        'x="310" text-anchor="middle"'
    )

    s += (
        f'<a href="{escape(repo["url"])}">'
        f'<rect x="245" y="177" width="110" height="25" '
        f'rx="12" fill="#111827"/>'
        f'{button_text}</a>'
    )

    save(f"repo-0{index}.svg", s + svg_end())


def render_graph(m, fonts, delay, animated):
    s = svg_start(
        1200, 190,
        "GitHub contribution graph",
        fonts, delay, animated
    )

    s += txt(
        42, 43, "THE CONTRIBUTION GRID",
        13, PURPLE, 700
    )

    s += txt(
        42, 75,
        f'{m["total"]:,} contributions in the last year',
        22, TEXT, 700, "heading"
    )

    today = date.today()
    first = today - timedelta(days=364)
    monday = first - timedelta(days=first.weekday())

    palette = [
        "#F1F5F9",
        "#CBD5E1",
        "#94A3B8",
        "#334155",
    ]

    max_count = max(m["days"].values()) if m["days"] else 1

    for i in range(53 * 7):
        day = monday + timedelta(days=i)

        if day < first or day > today:
            continue

        count = m["days"].get(day, 0)

        level = (
            0 if count == 0
            else min(3, max(1, int(count / max_count * 3) + 1))
        )

        x = 50 + (day - monday).days // 7 * 18
        y = 103 + day.weekday() * 18

        s += (
            f'<rect x="{x}" y="{y}" width="13" height="13" '
            f'rx="3" fill="{palette[level]}">'
            f'<title>{day.isoformat()}: {count} contributions</title>'
            f'</rect>'
        )

    s += txt(50, 180, "LESS", 10, MUTED, 500)

    for i, color in enumerate(palette):
        s += (
            f'<rect x="{100 + i * 23}" y="168" '
            f'width="13" height="13" rx="3" fill="{color}"/>'
        )

    s += txt(205, 180, "MORE", 10, MUTED, 500)

    save("contributions.svg", s + svg_end())


def render_section_title(fonts, delay, animated):
    s = svg_start(
        1200, 110,
        "What I'm building",
        fonts, delay, animated
    )

    s += txt(
        42, 45, "WHAT I'M BUILDING",
        13, PURPLE, 700
    )

    s += txt(
        42, 83,
        "Selected projects & experiments",
        27, TEXT, 700, "heading"
    )

    save("section-title.svg", s + svg_end())


def render_all(fonts):
    m = calculate_metrics(load_days())
    animated = not STATIC
    n = 0

    def delay():
        nonlocal n
        value = n * 0.52
        n += 1
        return value

    render_hero(fonts, delay(), animated)

    for i, item in enumerate(TILES, 1):
        render_tile(i, item, fonts, delay(), animated)

    render_activity(m, fonts, delay(), animated)

    render_section_title(fonts, delay(), animated)

    for i, repo in enumerate(REPOS, 1):
        render_repo(repo, i, fonts, delay(), animated)

    render_graph(m, fonts, delay(), animated)

    print(
        f"Rendered {len(list(OUT.glob('*.svg')))} SVG cards in {OUT}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-data", action="store_true")

    args = parser.parse_args()

    if args.refresh_data:
        refresh_contributions()

    with tempfile.TemporaryDirectory(
        prefix="profile-card-fonts-"
    ) as temp:
        render_all(subset_fonts(Path(temp)))


if __name__ == "__main__":
    main()
