"""XML and SVG utility functions."""

import re
from pathlib import Path


def escape_xml(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def parse_glyph_ref(value: str) -> tuple[str, str] | None:
    """Parse a glyph reference like $$mdi:play-pause$$.

    Args:
        value: String that may contain a glyph reference

    Returns:
        (source, name) tuple or None if not a glyph reference
    """
    match = re.match(r"^\$\$([^:]+):([^$]+)\$\$$", value)
    if match:
        return match.group(1), match.group(2)
    return None


def extract_glyph_defs(svg_content: str) -> str:
    """Extract glyph definitions from an SVG file.

    Finds all glyph SVG elements in the defs section.
    Pattern matches: <svg id="prefix:name">...<svg>...</svg></svg>

    Args:
        svg_content: Full SVG file content

    Returns:
        String containing all glyph definitions
    """
    glyph_pattern = re.compile(
        r'<svg id="[^"]+:[^"]+">\s*<svg[^>]*>.*?</svg>\s*</svg>', re.DOTALL
    )
    glyphs = glyph_pattern.findall(svg_content)
    return "\n".join(glyphs) if glyphs else ""


def calculate_corner_offsets(
    key_w: float = 60, key_h: float = 56, pad_x: float = 10, pad_y: float = 8
) -> tuple[int, int]:
    """Calculate corner text offsets from key center based on edge padding.

    Args:
        key_w: Key width (default: 60)
        key_h: Key height (default: 56)
        pad_x: Padding from left/right edges (minimum 2px for font clearance)
        pad_y: Padding from top/bottom edges (minimum 2px for font clearance)

    Returns:
        (x_offset, y_offset) - distances from key center to corner text
    """
    # Minimum 2px padding to account for font rendering
    min_pad = 2
    pad_x = max(pad_x, min_pad)
    pad_y = max(pad_y, min_pad)

    x_offset = int(key_w / 2 - pad_x)
    y_offset = int(key_h / 2 - pad_y)
    return x_offset, y_offset


def load_svg_file(path: Path) -> str:
    """Load SVG file content.

    Args:
        path: Path to SVG file

    Returns:
        SVG file content as string
    """
    return path.read_text()


def save_svg_file(path: Path, content: str) -> None:
    """Save SVG content to file.

    Args:
        path: Path to save SVG file
        content: SVG content to save
    """
    path.write_text(content)
