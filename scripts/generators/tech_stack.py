"""Generate a tech stack SVG with inline logos."""

import math
import os
from html import escape

from config import LOGO_DIR, TECH_STACK, THEME
from svg_utils import read_svg, svg_document

COLS: int = 6
CELL_W: int = 130
CELL_H: int = 105
ICON_SIZE: int = 52
PADDING_X: int = 28
PADDING_Y: int = 24
HEADER_H: int = 44
SECTION_GAP: int = 16

SVG_WIDTH: int = PADDING_X * 2 + COLS * CELL_W


def _section_height(item_count: int) -> int:
    """Height of one section (header + item rows)."""
    rows = math.ceil(item_count / COLS)
    return HEADER_H + rows * CELL_H


def _total_height() -> int:
    section_heights = [_section_height(len(items)) for _, _, items in TECH_STACK]
    gaps = SECTION_GAP * (len(TECH_STACK) - 1)
    return PADDING_Y * 2 + sum(section_heights) + gaps


def _render_header(name: str, y: int) -> list[str]:
    return [
        f'<text x="{PADDING_X}" y="{y + 16}" fill="{THEME["text"]}"'
        f' class="header">{escape(name)}</text>',
        f'<line x1="{PADDING_X}" y1="{y + HEADER_H - 8}"'
        f' x2="{SVG_WIDTH - PADDING_X}" y2="{y + HEADER_H - 8}"'
        f' stroke="{THEME["border"]}" stroke-width="1"/>',
    ]


def _resolve_logo(filename: str, folder: str) -> str:
    """Resolve a logo filename to an absolute path."""
    relative = filename if "/" in filename else f"{folder}/{filename}"
    return os.path.join(LOGO_DIR, relative)


def _render_item(logo_file: str, label: str, folder: str,
                 id_prefix: str, cx: float, cy: float) -> list[str]:
    parts = []

    path = _resolve_logo(logo_file, folder)
    viewbox, inner = read_svg(path, id_prefix)
    if inner:
        ix = cx - ICON_SIZE / 2
        iy = cy + 8
        parts.append(
            f'<svg x="{ix}" y="{iy}" width="{ICON_SIZE}" height="{ICON_SIZE}"'
            f' viewBox="{viewbox}">'
        )
        parts.append(inner)
        parts.append("</svg>")

    ly = cy + ICON_SIZE + 22
    parts.append(
        f'<text x="{cx}" y="{ly}" fill="{THEME["text_secondary"]}"'
        f' class="label" text-anchor="middle">{escape(label)}</text>'
    )
    return parts


def _render_section(section_idx: int, name: str, folder: str,
                    items: list[tuple[str, str]], y: int) -> list[str]:
    parts = _render_header(name, y)
    y += HEADER_H

    for idx, (logo_file, label) in enumerate(items):
        col = idx % COLS
        row = idx // COLS
        cx = PADDING_X + col * CELL_W + CELL_W / 2
        cy = y + row * CELL_H
        parts.extend(_render_item(
            logo_file, label, folder, f"i{section_idx}-{idx}", cx, cy
        ))

    return parts


def generate_svg() -> str:
    """Generate the complete tech stack SVG."""
    height = _total_height()
    font = THEME["font"]

    style = "\n".join([
        "<style>",
        f'  .header {{ font: bold 15px {font}; }}',
        f'  .label {{ font: 13px {font}; }}',
        "</style>",
    ])

    body_parts = [style]
    y = PADDING_Y

    for section_idx, (name, folder, items) in enumerate(TECH_STACK):
        body_parts.extend(_render_section(section_idx, name, folder, items, y))
        y += _section_height(len(items))
        if section_idx < len(TECH_STACK) - 1:
            y += SECTION_GAP

    return svg_document(SVG_WIDTH, height, "\n".join(body_parts))
