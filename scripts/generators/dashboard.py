"""Generate a GitHub profile dashboard SVG."""

import html

from config import THEME
from generators.contributions import (
    ContributionDay, _build_weeks, _render_cells_at,
    _render_day_labels_at, _render_month_labels_at,
    CELL_STEP,
)
from github_api import GitHubStats
from svg_utils import svg_document

PADDING = 24
WIDTH = 848
FONT = THEME["font"]


def _render_stats_row(stats: GitHubStats, y: int) -> list[str]:
    items: list[tuple[str, str]] = [
        (f"{stats.total_contributions:,}", "Contributions"),
        (f"{stats.repos}", "Repos"),
        (f"{stats.stars}", "Stars"),
    ]
    parts: list[str] = []
    spacing: float = (WIDTH - 2 * PADDING) / len(items)
    for i, (value, label) in enumerate(items):
        x: float = PADDING + spacing * i + spacing / 2
        parts.append(
            f'<text x="{x}" y="{y}" fill="{THEME["text"]}"'
            f' font-size="20" font-weight="bold" font-family="{FONT}"'
            f' text-anchor="middle">{html.escape(value)}</text>'
        )
        parts.append(
            f'<text x="{x}" y="{y + 18}" fill="{THEME["text_secondary"]}"'
            f' font-size="11" font-family="{FONT}"'
            f' text-anchor="middle">{html.escape(label)}</text>'
        )
    return parts


def _render_contribution_graph(days: list[ContributionDay], y: int) -> tuple[list[str], int]:
    weeks: list[list[ContributionDay]] = _build_weeks(days)
    grid_top: int = y + 16
    parts: list[str] = []
    parts.extend(_render_month_labels_at(weeks, grid_top))
    parts.extend(_render_day_labels_at(grid_top))
    parts.extend(_render_cells_at(weeks, grid_top))
    grid_bottom: int = grid_top + 7 * CELL_STEP
    return parts, grid_bottom


def _render_legend(y: int) -> list[str]:
    colors: dict[int, str] = THEME["contribution_levels"]
    parts: list[str] = []
    box: int = 10
    gap: int = 3
    label_less_w: int = 28
    label_more_w: int = 30
    legend_width: int = 5 * (box + gap) - gap
    total_w: int = label_less_w + legend_width + gap + label_more_w
    x: int = WIDTH - PADDING - total_w

    parts.append(
        f'<text x="{x}" y="{y + box - 1}" fill="{THEME["text_secondary"]}"'
        f' font-size="10" font-family="sans-serif">Less</text>'
    )
    x += label_less_w
    for level in range(5):
        parts.append(
            f'<rect x="{x}" y="{y}" width="{box}" height="{box}"'
            f' rx="2" fill="{colors[level]}"/>'
        )
        x += box + gap
    parts.append(
        f'<text x="{x}" y="{y + box - 1}" fill="{THEME["text_secondary"]}"'
        f' font-size="10" font-family="sans-serif">More</text>'
    )
    return parts


def _render_divider(y: int) -> str:
    return (
        f'<line x1="{PADDING}" y1="{y}" x2="{WIDTH - PADDING}" y2="{y}"'
        f' stroke="{THEME["border"]}" stroke-width="1"/>'
    )


def generate_svg(days: list[ContributionDay], total: int,
                 stats: GitHubStats) -> str:
    """Generate the complete dashboard SVG."""
    parts: list[str] = []
    y: int = PADDING + 4

    # Stats row
    parts.extend(_render_stats_row(stats, y + 16))
    y += 52

    parts.append(_render_divider(y))
    y += 8

    # Contribution graph
    graph_parts, graph_bottom = _render_contribution_graph(days, y)
    parts.extend(graph_parts)
    parts.extend(_render_legend(graph_bottom + 6))

    height: int = graph_bottom + 28 + PADDING

    return svg_document(WIDTH, height, "\n".join(parts))
