"""Generate a single terminal-style SVG combining dashboard + tech stack."""

import math
import os
from html import escape

from config import LOGO_DIR, TECH_STACK, THEME
from generators.contributions import ContributionDay, _build_weeks
from github_api import GitHubStats
from svg_utils import read_svg

LEVELS = THEME["contribution_levels"]
WIDTH = 840
PAD = 24
LINE_H = 22

# Tech stack grid within terminal
COLS = 6
CELL_W = 128
CELL_H = 100
ICON_SIZE = 48

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CHART_H = 100


# ── Shared render helpers ─────────────────────────────────────

def _prompt(y: int, text: str) -> list[str]:
    return [
        f'<text x="{PAD}" y="{y}" fill="{THEME["green"]}" font-size="13" font-family="{THEME["font_mono"]}">$ </text>',
        f'<text x="{PAD + 16}" y="{y}" fill="{THEME["text"]}" font-size="13" font-family="{THEME["font_mono"]}">{escape(text)}</text>',
    ]


# ── Title bar ─────────────────────────────────────────────────

def _render_titlebar() -> list[str]:
    parts: list[str] = []
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="36" fill="{THEME["titlebar"]}" rx="8"/>')
    parts.append(f'<rect x="0" y="18" width="{WIDTH}" height="18" fill="{THEME["titlebar"]}"/>')
    for i, color in enumerate(["#28c840", "#febc2e", "#ff5f57"]):
        parts.append(f'<circle cx="{WIDTH - 20 - i * 20}" cy="18" r="6" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="22" fill="{THEME["text_dim"]}" font-size="12"'
        f' font-family="{THEME["font_mono"]}" text-anchor="middle">scorpio-99 — bash</text>'
    )
    return parts


# ── Line Chart ────────────────────────────────────────────────

def _week_total(week: list[ContributionDay]) -> int:
    return sum(d.level for d in week)


def _render_chart(weeks: list[list[ContributionDay]], x0: float, y0: float) -> tuple[list[str], int]:
    parts: list[str] = []
    graph_w = WIDTH - 2 * PAD - 40
    step = graph_w / max(len(weeks) - 1, 1)

    # Month labels
    seen: set[str] = set()
    for col, week in enumerate(weeks):
        key = week[0].month_key
        if key in seen:
            continue
        seen.add(key)
        label = MONTHS[week[0].date.month - 1]
        parts.append(
            f'<text x="{x0 + col * step}" y="{y0}" fill="{THEME["text_dim"]}"'
            f' font-size="9" font-family="{THEME["font_mono"]}">{label}</text>'
        )

    y0 += 14
    baseline = y0 + CHART_H
    max_total = max(_week_total(w) for w in weeks) or 1

    # Grid lines
    for i in range(3):
        gy = y0 + i * (CHART_H / 2)
        parts.append(
            f'<line x1="{x0}" y1="{gy}" x2="{x0 + graph_w}" y2="{gy}"'
            f' stroke="{THEME["border_light"]}" stroke-width="0.5"/>'
        )

    # Build points
    points = []
    for col, week in enumerate(weeks):
        total = _week_total(week)
        x = x0 + col * step
        y = baseline - (total / max_total) * CHART_H
        points.append((x, y))

    # Fill area
    if points:
        poly = " ".join(f"{x},{y}" for x, y in points)
        poly = f"{x0},{baseline} {poly} {points[-1][0]},{baseline}"
        parts.append(
            f'<polygon points="{poly}" fill="{THEME["green"]}" opacity="0.15"/>'
        )

    # Line
    if len(points) > 1:
        path = f"M{points[0][0]},{points[0][1]}"
        for x, y in points[1:]:
            path += f" L{x},{y}"
        parts.append(
            f'<path d="{path}" fill="none" stroke="{THEME["green"]}" stroke-width="1.5"/>'
        )

    # Dots at peaks
    for x, y in points:
        if y < baseline - CHART_H * 0.5:
            parts.append(f'<circle cx="{x}" cy="{y}" r="2" fill="{THEME["green"]}"/>')

    return parts, CHART_H + 24


# ── Tech stack section ────────────────────────────────────────

def _resolve_logo(filename: str, folder: str) -> str:
    relative = filename if "/" in filename else f"{folder}/{filename}"
    return os.path.join(LOGO_DIR, relative)


def _render_tech_section(section_idx: int, name: str, folder: str,
                         items: list[tuple[str, str]], x0: float, y: int) -> tuple[list[str], int]:
    parts: list[str] = []

    parts.append(
        f'<text x="{x0}" y="{y}" fill="{THEME["green"]}" font-size="13"'
        f' font-family="{THEME["font_mono"]}">// {escape(name)}</text>'
    )
    parts.append(
        f'<line x1="{x0}" y1="{y + 6}" x2="{x0 + COLS * CELL_W}" y2="{y + 6}"'
        f' stroke="{THEME["border_light"]}" stroke-width="0.5"/>'
    )
    y += 20

    rows = math.ceil(len(items) / COLS)
    for idx, (logo_file, label) in enumerate(items):
        col = idx % COLS
        row = idx // COLS
        cx = x0 + col * CELL_W + CELL_W / 2
        cy = y + row * CELL_H

        path = _resolve_logo(logo_file, folder)
        viewbox, inner = read_svg(path, f"i{section_idx}-{idx}")
        if inner:
            ix = cx - ICON_SIZE / 2
            iy = cy + 4
            parts.append(
                f'<svg x="{ix}" y="{iy}" width="{ICON_SIZE}" height="{ICON_SIZE}"'
                f' viewBox="{viewbox}">'
            )
            parts.append(inner)
            parts.append("</svg>")

        ly = cy + ICON_SIZE + 20
        parts.append(
            f'<text x="{cx}" y="{ly}" fill="{THEME["text"]}" font-size="11"'
            f' font-family="{THEME["font_mono"]}" text-anchor="middle">{escape(label)}</text>'
        )

    y += rows * CELL_H + 8
    return parts, y


# ── Streak & activity stats ───────────────────────────────────

def _calculate_streak(days: list[ContributionDay]) -> tuple[int, int]:
    """Return (current_streak, longest_streak) in days."""
    if not days:
        return 0, 0
    longest = 0
    streak = 0
    prev_date = None
    for day in days:
        if day.level > 0:
            if prev_date and (day.date - prev_date).days == 1:
                streak += 1
            else:
                streak = 1
            longest = max(longest, streak)
        else:
            streak = 0
        prev_date = day.date
    return streak, longest


def _most_productive_day(days: list[ContributionDay]) -> str:
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    counts = [0] * 7
    for day in days:
        if day.level > 0:
            counts[day.date.weekday()] += 1
    return names[counts.index(max(counts))]


def _avg_per_week(days: list[ContributionDay]) -> float:
    weeks = _build_weeks(days)
    if not weeks:
        return 0
    active = sum(1 for w in weeks if any(d.level > 0 for d in w))
    total = sum(d.level for d in days)
    return round(total / max(active, 1), 1)


# ── Info line helper ──────────────────────────────────────────

def _info_line(y: int, key: str, val: str) -> list[str]:
    return [
        f'<text x="{PAD + 16}" y="{y}" fill="{THEME["text_dim"]}" font-size="12" font-family="{THEME["font_mono"]}">{escape(key)}</text>',
        f'<text x="{PAD + 200}" y="{y}" fill="{THEME["text"]}" font-size="12" font-family="{THEME["font_mono"]}">{escape(val)}</text>',
    ]


# ── Main generate ─────────────────────────────────────────────

def generate_svg(days: list[ContributionDay], total: int,
                 stats: GitHubStats) -> str:
    """Generate the complete terminal-style profile SVG."""
    weeks = _build_weeks(days)
    parts: list[str] = []

    parts.extend(_render_titlebar())

    y = 56

    # ── neofetch ──
    parts.extend(_prompt(y, "neofetch"))
    y += LINE_H + 32

    items = [
        (f"{stats.total_contributions:,}", "contributions"),
        (str(stats.repos), "own repos"),
        (str(stats.stars), "stars"),
    ]
    spacing = (WIDTH - 2 * PAD) / len(items)
    for i, (val, label) in enumerate(items):
        x = PAD + spacing * i + spacing / 2
        parts.append(
            f'<text x="{x}" y="{y}" fill="{THEME["text"]}" font-size="36" font-weight="bold"'
            f' font-family="{THEME["font_mono"]}" text-anchor="middle">{escape(val)}</text>'
        )
        parts.append(
            f'<text x="{x}" y="{y + 20}" fill="{THEME["text_dim"]}" font-size="11"'
            f' font-family="{THEME["font_mono"]}" text-anchor="middle">{escape(label)}</text>'
        )

    y += 56

    # ── contributions ──
    parts.extend(_prompt(y, "cat contributions.log"))
    y += LINE_H + 12

    chart_parts, chart_h = _render_chart(weeks, PAD + 16, y)
    parts.extend(chart_parts)
    y += chart_h + 20

    # ── uptime / streak ──
    current_streak, longest_streak = _calculate_streak(days)
    best_day = _most_productive_day(days)
    avg = _avg_per_week(days)

    parts.extend(_prompt(y, "uptime"))
    y += LINE_H + 10

    for key, val in [
        ("current streak", f"{current_streak} days"),
        ("longest streak", f"{longest_streak} days"),
        ("best day", best_day),
        ("top languages", ", ".join(stats.top_languages)),
        ("member since", str(stats.member_since)),
    ]:
        parts.extend(_info_line(y, key, val))
        y += LINE_H

    y += 16

    # ── tech stack ──
    parts.extend(_prompt(y, "ls tools"))
    y += LINE_H + 14

    tech_x = PAD + 16
    for section_idx, (name, folder, items) in enumerate(TECH_STACK):
        section_parts, y = _render_tech_section(section_idx, name, folder, items, tech_x, y)
        parts.extend(section_parts)
        y += 8

    # ── cursor ──
    y += 4
    parts.append(
        f'<text x="{PAD}" y="{y}" fill="{THEME["green"]}" font-size="13"'
        f' font-family="{THEME["font_mono"]}">$ <tspan fill="{THEME["text_dim"]}">_</tspan></text>'
    )
    y += PAD

    inner = "\n".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{y}"'
        f' viewBox="0 0 {WIDTH} {y}">\n'
        f'<rect width="{WIDTH}" height="{y}" fill="{THEME["bg_alt"]}" rx="8"/>\n'
        f'{inner}\n</svg>'
    )
