"""Fetch GitHub contribution data."""

import re
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from urllib.request import urlopen


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
