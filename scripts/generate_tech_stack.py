"""Entry point: generate the tech stack SVG."""

from config import OUTPUT_TECH_STACK
from generators.tech_stack import generate_svg
from svg_utils import write_svg


def main():
    svg = generate_svg()
    write_svg(OUTPUT_TECH_STACK, svg)


if __name__ == "__main__":
    main()
