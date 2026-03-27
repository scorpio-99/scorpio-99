"""Fetch GitHub contribution data and generate an SVG graph."""

import re
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from urllib.request import urlopen

from config import THEME
from svg_utils import svg_document

CELL_SIZE = 11
CELL_GAP = 3
CELL_STEP = CELL_SIZE + CELL_GAP
LEFT_MARGIN = 32
TOP_MARGIN = 22
LABEL_OFFSET = 8
FOOTER_HEIGHT = 24

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


@dataclass
class ContributionDay:
    date: datetime
    level: int

    @property
    def weekday(self) -> int:
        """GitHub-style weekday (Sun=0, Mon=1, ..., Sat=6)."""
        return (self.date.weekday() + 1) % 7

    @property
    def month_key(self) -> str:
        return f"{self.date.year}-{self.date.month:02d}"


class _ContributionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.contributions: list[ContributionDay] = []
        self.total: int = 0
        self._in_h2: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h2":
            self._in_h2 = True
            return
        if tag != "td":
            return
        attr_dict = dict(attrs)
        if "ContributionCalendar-day" not in attr_dict.get("class", ""):
            return
        date_str = attr_dict.get("data-date")
        level = attr_dict.get("data-level")
        if date_str and level is not None:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            self.contributions.append(ContributionDay(date=dt, level=int(level)))

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2":
            self._in_h2 = False

    def handle_data(self, data: str) -> None:
        if self._in_h2 and "contribution" in data:
            match = re.search(r"([\d,]+)\s+contribution", data)
            if match:
                self.total = int(match.group(1).replace(",", ""))


def fetch_contributions(username: str) -> tuple[list[ContributionDay], int]:
    """Fetch contribution data from GitHub's public profile page.

    Returns (days, total_contributions).
    """
    url = f"https://github.com/users/{username}/contributions"
    with urlopen(url, timeout=30) as resp:
        html = resp.read().decode("utf-8")
    if "ContributionCalendar" not in html:
        raise ValueError(f"Response from {url} does not contain contribution data")
    parser = _ContributionParser()
    parser.feed(html)
    days = sorted(parser.contributions, key=lambda c: c.date)
    return days, parser.total


def _build_weeks(days: list[ContributionDay]) -> list[list[ContributionDay]]:
    """Group contribution days into weeks (new week starts on Sunday)."""
    if not days:
        return []
    weeks: list[list[ContributionDay]] = []
    current: list[ContributionDay] = []

    for day in days:
        if day.weekday == 0 and current:
            weeks.append(current)
            current = []
        current.append(day)

    if current:
        weeks.append(current)
    return weeks


def _render_day_labels_at(grid_top: int) -> list[str]:
    parts: list[str] = []
    for row, label in DAY_LABELS.items():
        y = grid_top + row * CELL_STEP + CELL_SIZE - 1
        parts.append(
            f'<text x="{LEFT_MARGIN - 6}" y="{y}" fill="{THEME["text_secondary"]}"'
            f' font-size="10" font-family="sans-serif" text-anchor="end">{label}</text>'
        )
    return parts


def _render_month_labels_at(weeks: list[list[ContributionDay]], grid_top: int) -> list[str]:
    parts: list[str] = []
    seen: set[str] = set()
    for col, week in enumerate(weeks):
        key = week[0].month_key
        if key in seen:
            continue
        seen.add(key)
        label = MONTHS[week[0].date.month - 1]
        x = LEFT_MARGIN + col * CELL_STEP
        parts.append(
            f'<text x="{x}" y="{grid_top - LABEL_OFFSET}" fill="{THEME["text_secondary"]}"'
            f' font-size="10" font-family="sans-serif">{label}</text>'
        )
    return parts


def _render_cells_at(weeks: list[list[ContributionDay]], grid_top: int) -> list[str]:
    colors: dict[int, str] = THEME["contribution_levels"]
    parts: list[str] = []
    for col, week in enumerate(weeks):
        for day in week:
            x = LEFT_MARGIN + col * CELL_STEP
            y = grid_top + day.weekday * CELL_STEP
            color = colors.get(day.level, colors[0])
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}"'
                f' rx="2" fill="{color}"/>'
            )
    return parts


def _render_total(total: int, width: int) -> list[str]:
    text = f"{total:,} contributions in the last year"
    return [
        f'<text x="{LEFT_MARGIN}" y="{LABEL_OFFSET + 2}" fill="{THEME["text_secondary"]}"'
        f' font-size="11" font-family="sans-serif">{text}</text>',
    ]


def _render_legend(width: int, grid_bottom: int) -> list[str]:
    colors: dict[int, str] = THEME["contribution_levels"]
    parts: list[str] = []
    y: int = grid_bottom + 10
    box: int = 10
    gap: int = 3

    legend_width = 5 * (box + gap) - gap
    label_less_w = 28
    label_more_w = 30
    total_w = label_less_w + legend_width + gap + label_more_w
    x = width - total_w - 8

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


def generate_svg(days: list[ContributionDay], total: int) -> str:
    """Generate an SVG contribution graph."""
    weeks = _build_weeks(days)

    grid_top = TOP_MARGIN + 12
    width = LEFT_MARGIN + len(weeks) * CELL_STEP + 2
    grid_bottom = grid_top + 7 * CELL_STEP
    height = grid_bottom + FOOTER_HEIGHT

    body_parts: list[str] = []
    body_parts.extend(_render_total(total, width))
    body_parts.extend(_render_day_labels_at(grid_top))
    body_parts.extend(_render_month_labels_at(weeks, grid_top))
    body_parts.extend(_render_cells_at(weeks, grid_top))
    body_parts.extend(_render_legend(width, grid_bottom))

    return svg_document(width, height, "\n".join(body_parts))
