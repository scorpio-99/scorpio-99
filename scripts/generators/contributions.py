"""Fetch GitHub contribution data and generate an SVG graph."""

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
    def __init__(self):
        super().__init__()
        self.contributions: list[ContributionDay] = []

    def handle_starttag(self, tag, attrs):
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


def fetch_contributions(username: str) -> list[ContributionDay]:
    """Fetch contribution data from GitHub's public profile page."""
    url = f"https://github.com/users/{username}/contributions"
    with urlopen(url) as resp:
        html = resp.read().decode("utf-8")
    parser = _ContributionParser()
    parser.feed(html)
    return sorted(parser.contributions, key=lambda c: c.date)


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


def _render_day_labels() -> list[str]:
    parts = []
    for row, label in DAY_LABELS.items():
        y = TOP_MARGIN + row * CELL_STEP + CELL_SIZE - 1
        parts.append(
            f'<text x="{LEFT_MARGIN - 6}" y="{y}" fill="{THEME["text_secondary"]}"'
            f' font-size="10" font-family="sans-serif" text-anchor="end">{label}</text>'
        )
    return parts


def _render_month_labels(weeks: list[list[ContributionDay]]) -> list[str]:
    parts = []
    seen: set[str] = set()
    for col, week in enumerate(weeks):
        key = week[0].month_key
        if key in seen:
            continue
        seen.add(key)
        label = MONTHS[week[0].date.month - 1]
        x = LEFT_MARGIN + col * CELL_STEP
        parts.append(
            f'<text x="{x}" y="{TOP_MARGIN - LABEL_OFFSET}" fill="{THEME["text_secondary"]}"'
            f' font-size="10" font-family="sans-serif">{label}</text>'
        )
    return parts


def _render_cells(weeks: list[list[ContributionDay]]) -> list[str]:
    colors = THEME["contribution_levels"]
    parts = []
    for col, week in enumerate(weeks):
        for day in week:
            x = LEFT_MARGIN + col * CELL_STEP
            y = TOP_MARGIN + day.weekday * CELL_STEP
            color = colors.get(day.level, colors[0])
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}"'
                f' rx="2" fill="{color}"/>'
            )
    return parts


def generate_svg(days: list[ContributionDay]) -> str:
    """Generate an SVG contribution graph."""
    weeks = _build_weeks(days)

    width = LEFT_MARGIN + len(weeks) * CELL_STEP + 2
    height = TOP_MARGIN + 7 * CELL_STEP + 2

    body_parts = []
    body_parts.extend(_render_day_labels())
    body_parts.extend(_render_month_labels(weeks))
    body_parts.extend(_render_cells(weeks))

    return svg_document(width, height, "\n".join(body_parts))
