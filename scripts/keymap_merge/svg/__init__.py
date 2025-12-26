"""SVG manipulation utilities for keymap post-processing."""

from .utils import escape_xml, parse_glyph_ref, extract_glyph_defs, calculate_corner_offsets
from .css import generate_corner_css
from .injector import CornerInjector, inject_corner_legends
from .combiner import append_svg_below, merge_svg_defs

__all__ = [
    # Utils
    "escape_xml",
    "parse_glyph_ref",
    "extract_glyph_defs",
    "calculate_corner_offsets",
    # CSS
    "generate_corner_css",
    # Injector
    "CornerInjector",
    "inject_corner_legends",
    # Combiner
    "append_svg_below",
    "merge_svg_defs",
]
