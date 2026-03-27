"""Shared SVG utility functions."""

import re
import sys
from html import escape

from config import THEME

# Event handler attributes to strip from untrusted SVG content.
_EVENT_HANDLER_RE = re.compile(
    r'\s+on[a-z]+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)',
    re.IGNORECASE,
)


def _sanitize_svg(content: str) -> str:
    """Remove dangerous elements and attributes from SVG content."""
    content = re.sub(r"<script[\s>].*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<style[\s>].*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)
    content = _EVENT_HANDLER_RE.sub("", content)
    return content


def _escape_viewbox(value: str) -> str:
    """Escape a viewBox value so it cannot break out of the attribute."""
    return escape(value, quote=True)


def read_svg(path: str, id_prefix: str) -> tuple[str, str]:
    """Read an SVG file and return (viewBox, inner_content) with prefixed IDs.

    Args:
        path: Absolute path to the SVG file.
        id_prefix: Prefix to add to all IDs to avoid conflicts.
    """
    try:
        with open(path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Warning: {path} not found, skipping", file=sys.stderr)
        return "", ""

    content = _sanitize_svg(content)

    vb_match = re.search(r'viewBox="([^"]*)"', content)
    viewbox = _escape_viewbox(vb_match.group(1) if vb_match else "0 0 128 128")

    content = re.sub(r"<\?xml[^?]*\?>", "", content)
    content = re.sub(r"<!DOCTYPE[^>]*>", "", content)

    inner_match = re.search(r"<svg[^>]*>(.*)</svg>", content, re.DOTALL)
    if not inner_match:
        return viewbox, ""
    inner = inner_match.group(1).strip()

    inner = _prefix_ids(inner, id_prefix)
    return viewbox, inner


def _prefix_ids(svg_content: str, prefix: str) -> str:
    """Prefix all IDs and their references to avoid cross-logo conflicts."""
    ids = set(re.findall(r'id="([^"]*)"', svg_content))
    for old_id in ids:
        new_id = f"{prefix}-{old_id}"
        svg_content = re.sub(
            rf'id="{re.escape(old_id)}"', f'id="{new_id}"', svg_content
        )
        svg_content = re.sub(
            rf"url\(#{re.escape(old_id)}\)", f"url(#{new_id})", svg_content
        )
        svg_content = re.sub(
            rf'href="#{re.escape(old_id)}"', f'href="#{new_id}"', svg_content
        )
        svg_content = re.sub(
            rf'xlink:href="#{re.escape(old_id)}"',
            f'xlink:href="#{new_id}"',
            svg_content,
        )
    return svg_content


def svg_document(width: int, height: int, body: str) -> str:
    """Wrap SVG body in a complete document with dark background."""
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'
        f' width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{THEME["bg"]}" rx="6"/>',
        body,
        "</svg>",
    ])


def write_svg(path: str, content: str) -> None:
    """Write SVG content to a file."""
    with open(path, "w") as f:
        f.write(content)
    print(f"Generated {path}")
