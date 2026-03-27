"""Entry point: generate the GitHub contribution graph SVG."""

import sys

from config import OUTPUT_CONTRIBUTION_GRAPH, USERNAME
from generators.contributions import fetch_contributions, generate_svg
from svg_utils import write_svg


def main():
    contributions = fetch_contributions(USERNAME)
    if not contributions:
        print("No contribution data found.", file=sys.stderr)
        sys.exit(1)
    svg = generate_svg(contributions)
    write_svg(OUTPUT_CONTRIBUTION_GRAPH, svg)


if __name__ == "__main__":
    main()
