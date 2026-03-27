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
FONT_MONO = "Consolas, Monaco, monospace"
GREEN = "#39d353"
DIM = "#8b949e"
WHITE = "#ffffff"
BG = "#161b22"
TITLEBAR_BG = "#21262d"
BORDER = "#30363d"

# Tech stack grid within terminal
COLS = 6
CELL_W = 128
CELL_H = 100
ICON_SIZE = 48


# ── Shared render helpers ─────────────────────────────────────

def _prompt(y: int, text: str) -> list[str]:
    return [
        f'<text x="{PAD}" y="{y}" fill="{GREEN}" font-size="13" font-family="{FONT_MONO}">$ </text>',
        f'<text x="{PAD + 16}" y="{y}" fill="{WHITE}" font-size="13" font-family="{FONT_MONO}">{escape(text)}</text>',
    ]


def _info(y: int, key: str, val: str) -> list[str]:
    return [
        f'<text x="{PAD + 16}" y="{y}" fill="{GREEN}" font-size="13" font-family="{FONT_MONO}">{escape(key)}</text>',
        f'<text x="{PAD + 180}" y="{y}" fill="{WHITE}" font-size="13" font-family="{FONT_MONO}">{escape(val)}</text>',
    ]


def _comment(y: int, text: str) -> list[str]:
    return [
        f'<text x="{PAD + 16}" y="{y}" fill="{DIM}" font-size="12" font-family="{FONT_MONO}">{escape(text)}</text>',
    ]


# ── Title bar ─────────────────────────────────────────────────

def _render_titlebar() -> list[str]:
    parts: list[str] = []
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="36" fill="{TITLEBAR_BG}" rx="8"/>')
    parts.append(f'<rect x="0" y="18" width="{WIDTH}" height="18" fill="{TITLEBAR_BG}"/>')
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        parts.append(f'<circle cx="{20 + i * 20}" cy="18" r="6" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="22" fill="{DIM}" font-size="12"'
        f' font-family="{FONT_MONO}" text-anchor="middle">scorpio-99 — bash</text>'
    )
    return parts


# ── Heatmap ───────────────────────────────────────────────────

def _render_heatmap(weeks: list[list[ContributionDay]], x0: float, y0: float) -> list[str]:
    parts: list[str] = []
    cell, gap = 7, 2
    step = cell + gap
    for col, week in enumerate(weeks):
        for day in week:
            parts.append(
                f'<rect x="{x0 + col * step}" y="{y0 + day.weekday * step}"'
                f' width="{cell}" height="{cell}" rx="1.5"'
                f' fill="{LEVELS.get(day.level, LEVELS[0])}"/>'
            )
    return parts


# ── Tech stack section ────────────────────────────────────────

def _resolve_logo(filename: str, folder: str) -> str:
    relative = filename if "/" in filename else f"{folder}/{filename}"
    return os.path.join(LOGO_DIR, relative)


def _render_tech_section(section_idx: int, name: str, folder: str,
                         items: list[tuple[str, str]], x0: float, y: int) -> tuple[list[str], int]:
    parts: list[str] = []

    # Section header as comment
    parts.append(
        f'<text x="{x0}" y="{y}" fill="{GREEN}" font-size="13"'
        f' font-family="{FONT_MONO}">// {escape(name)}</text>'
    )
    parts.append(
        f'<line x1="{x0}" y1="{y + 6}" x2="{x0 + COLS * CELL_W}" y2="{y + 6}"'
        f' stroke="{BORDER}" stroke-width="0.5"/>'
    )
    y += 20

    rows = math.ceil(len(items) / COLS)
    for idx, (logo_file, label) in enumerate(items):
        col = idx % COLS
        row = idx // COLS
        cx = x0 + col * CELL_W + CELL_W / 2
        cy = y + row * CELL_H

        # Logo
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

        # Label
        ly = cy + ICON_SIZE + 20
        parts.append(
            f'<text x="{cx}" y="{ly}" fill="{WHITE}" font-size="11"'
            f' font-family="{FONT_MONO}" text-anchor="middle">{escape(label)}</text>'
        )

    y += rows * CELL_H + 8
    return parts, y


# ── Main generate ─────────────────────────────────────────────

def generate_svg(days: list[ContributionDay], total: int,
                 stats: GitHubStats) -> str:
    """Generate the complete terminal-style profile SVG."""
    weeks = _build_weeks(days)
    parts: list[str] = []

    # Title bar
    parts.extend(_render_titlebar())

    y = 56

    # ── neofetch ──
    parts.extend(_prompt(y, "neofetch"))
    y += LINE_H + 16

    items = [
        (f"{stats.total_contributions:,}", "contributions"),
        (str(stats.repos), "repos"),
        (str(stats.stars), "stars"),
        (str(stats.followers), "followers"),
    ]
    spacing = (WIDTH - 2 * PAD) / len(items)
    for i, (val, label) in enumerate(items):
        x = PAD + spacing * i + spacing / 2
        parts.append(
            f'<text x="{x}" y="{y}" fill="{WHITE}" font-size="28" font-weight="bold"'
            f' font-family="{FONT_MONO}" text-anchor="middle">{escape(val)}</text>'
        )
        parts.append(
            f'<text x="{x}" y="{y + 20}" fill="{DIM}" font-size="11"'
            f' font-family="{FONT_MONO}" text-anchor="middle">{escape(label)}</text>'
        )

    y += 56

    # ── contributions ──
    parts.extend(_prompt(y, "cat contributions.log"))
    y += LINE_H + 12

    parts.extend(_render_heatmap(weeks, PAD + 16, y))
    y += 7 * 9 + 36

    # ── tech stack ──
    parts.extend(_prompt(y, "ls tools/"))
    y += LINE_H + 12

    tech_x = PAD + 16
    for section_idx, (name, folder, items) in enumerate(TECH_STACK):
        section_parts, y = _render_tech_section(section_idx, name, folder, items, tech_x, y)
        parts.extend(section_parts)
        y += 8

    # ── cursor ──
    y += 4
    parts.append(
        f'<text x="{PAD}" y="{y}" fill="{GREEN}" font-size="13"'
        f' font-family="{FONT_MONO}">$ <tspan fill="{DIM}">_</tspan></text>'
    )
    y += PAD

    # Build SVG
    inner = "\n".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{y}"'
        f' viewBox="0 0 {WIDTH} {y}">\n'
        f'<rect width="{WIDTH}" height="{y}" fill="{BG}" rx="8"/>\n'
        f'{inner}\n</svg>'
    )
