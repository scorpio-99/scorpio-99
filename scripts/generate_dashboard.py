"""Entry point: generate the GitHub profile dashboard SVG."""

import sys

from config import OUTPUT_DASHBOARD, USERNAME
from generators.contributions import fetch_contributions
from generators.dashboard import generate_svg
from github_api import fetch_stats
from svg_utils import write_svg


def main():
    days, total = fetch_contributions(USERNAME)
    if not days:
        print("No contribution data found.", file=sys.stderr)
        sys.exit(1)
    stats = fetch_stats(USERNAME)
    svg = generate_svg(days, total, stats)
    write_svg(OUTPUT_DASHBOARD, svg)


if __name__ == "__main__":
    main()
