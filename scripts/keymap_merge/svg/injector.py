"""SVG corner legend injection."""

import re
from pathlib import Path
from typing import Callable

import yaml

from ..config import InjectorConfig, ThemeColors
from .css import generate_corner_css
from .utils import escape_xml, parse_glyph_ref, extract_glyph_defs, calculate_corner_offsets


class GlyphMixin:
    """Mixin for glyph element generation."""

    # Glyph position offsets by corner class
    GLYPH_POSITIONS: dict[str, Callable[[int, int, int], tuple[int, int]]] = {
        "tl": lambda x, y, gs: (x, y),
        "tr": lambda x, y, gs: (x - gs, y),
        "bl": lambda x, y, gs: (x, y - gs),
        "br": lambda x, y, gs: (x - gs, y - gs),
    }

    def make_glyph_element(
        self,
        glyph_ref: tuple[str, str],
        x: int,
        y: int,
        css_class: str,
        glyph_size: int,
        fill_color: str,
        extra_class: str = "",
    ) -> str:
        """Create a <use> element for a glyph icon.

        Args:
            glyph_ref: (source, name) tuple from parse_glyph_ref
            x: X coordinate (center-relative)
            y: Y coordinate (center-relative)
            css_class: Corner class (tl/tr/bl/br)
            glyph_size: Size in pixels
            fill_color: Fill color for the glyph
            extra_class: Additional CSS class (e.g., "hidden")

        Returns:
            SVG <use> element string
        """
        source, name = glyph_ref
        glyph_id = f"{source}:{name}"
        half = glyph_size // 2

        pos_func = self.GLYPH_POSITIONS.get(css_class, lambda x, y, gs: (x - half, y - half))
        gx, gy = pos_func(x, y, glyph_size)

        return (
            f'<use href="#{glyph_id}" xlink:href="#{glyph_id}" '
            f'x="{gx}" y="{gy}" height="{glyph_size}" width="{glyph_size}" '
            f'fill="{fill_color}" class="glyph {css_class}{extra_class}"/>'
        )


class CornerInjector(GlyphMixin):
    """Injects corner legend elements into SVG key groups.

    Used as a regex substitution callback. Holds pre-computed state to avoid
    recreating closures for each key match. Supports both text and glyph icons.

    Attributes:
        layer_keys: List of key definitions from merged.yaml
        x_offset, y_offset: Pixel offsets from key center to corners
        hide_set: Values to render as transparent (e.g., modifier symbols)
        fill_colors: Dict mapping corner positions (tl/tr/bl/br) to hex colors
        glyph_size: Size in pixels for corner glyph icons
    """

    def __init__(
        self,
        layer_keys: list,
        x_offset: int,
        y_offset: int,
        y_offset_bottom: int,
        hide_set: set[str],
        fill_colors: dict[str, str],
        glyph_size: int = 11,
    ):
        self.layer_keys = layer_keys
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.y_offset_bottom = y_offset_bottom
        self.hide_set = hide_set
        self.fill_colors = fill_colors
        self.glyph_size = glyph_size

    @classmethod
    def from_config(
        cls,
        layer_keys: list,
        config: InjectorConfig,
    ) -> "CornerInjector":
        """Create CornerInjector from configuration.

        Args:
            layer_keys: List of key definitions from merged.yaml
            config: Injection configuration

        Returns:
            Configured CornerInjector instance
        """
        x_offset, y_offset = calculate_corner_offsets(
            config.key_w, config.key_h, config.pad_x, config.pad_y
        )
        y_offset_bottom = y_offset + 1  # Adjustment for text-after-edge baseline

        fill_colors = {
            "tl": config.colors.tl,
            "tr": config.colors.tr,
            "bl": config.colors.bl,
            "br": config.colors.br,
        }

        return cls(
            layer_keys=layer_keys,
            x_offset=x_offset,
            y_offset=y_offset,
            y_offset_bottom=y_offset_bottom,
            hide_set=set(config.corner_hide),
            fill_colors=fill_colors,
            glyph_size=config.glyph_size,
        )

    def make_corner_element(self, value: str, x: int, y: int, css_class: str) -> str:
        """Create a text or use element for a corner legend.

        Args:
            value: Legend value (text or glyph reference)
            x: X coordinate (center-relative)
            y: Y coordinate (center-relative)
            css_class: Corner class (tl/tr/bl/br)

        Returns:
            SVG element string (text or use)
        """
        extra_class = " hidden" if str(value) in self.hide_set else ""
        glyph = parse_glyph_ref(str(value))

        if glyph:
            return self.make_glyph_element(
                glyph, x, y, css_class, self.glyph_size,
                self.fill_colors.get(css_class, "#000"), extra_class
            )
        else:
            return f'<text x="{x}" y="{y}" class="{css_class}{extra_class}">{escape_xml(str(value))}</text>'

    def inject(self, match: re.Match) -> str:
        """Regex substitution callback for key groups.

        Args:
            match: Regex match containing key group

        Returns:
            Modified key group with corner elements injected
        """
        opening_tag = match.group(1)
        keypos = int(match.group(2))
        content = match.group(3)
        closing_tag = match.group(4)

        if keypos >= len(self.layer_keys):
            return match.group(0)

        key = self.layer_keys[keypos]
        if not isinstance(key, dict):
            return match.group(0)

        # Build corner elements using pre-computed specs
        corner_specs = [
            ("tl", -self.x_offset, -self.y_offset),
            ("tr", self.x_offset, -self.y_offset),
            ("bl", -self.x_offset, self.y_offset_bottom),
            ("br", self.x_offset, self.y_offset_bottom),
        ]

        corner_elements = [
            self.make_corner_element(key[corner], x, y, corner)
            for corner, x, y in corner_specs
            if key.get(corner)
        ]

        if not corner_elements:
            return match.group(0)

        new_content = content + "\n" + "\n".join(corner_elements)
        return opening_tag + new_content + closing_tag


def inject_corner_legends(
    svg_content: str,
    merged_yaml_path: Path,
    config: InjectorConfig,
    glyph_svg_path: Path | None = None,
) -> str:
    """Inject corner legend text elements and theme colors into SVG.

    Reads tl/tr/bl/br values from merged.yaml and adds them as text/glyph
    elements at corner positions. Also injects CSS for theme colors.

    Args:
        svg_content: The SVG content from keymap-drawer
        merged_yaml_path: Path to merged.yaml with tl/tr/bl/br values
        config: Injection configuration
        glyph_svg_path: Path to SVG with glyph definitions (e.g., base.svg)

    Returns:
        Modified SVG content with corner legends injected
    """
    # Load merged YAML to get corner values
    with open(merged_yaml_path) as f:
        merged = yaml.safe_load(f)

    layer_keys = merged.get("layers", {}).get("merged", [])

    # Extract glyph defs from source SVG if provided
    glyph_defs = ""
    if glyph_svg_path and glyph_svg_path.exists():
        source_svg = glyph_svg_path.read_text()
        glyph_defs = extract_glyph_defs(source_svg)

    # Generate CSS for corner styling
    corner_css = generate_corner_css(config.colors, config.glyph_size)

    # Insert CSS before closing </style>
    if "</style>" in svg_content:
        svg_content = svg_content.replace("</style>", corner_css + "</style>")

    # Insert glyph defs if we have them and they're not already present
    if glyph_defs and '<svg id="mdi:' not in svg_content:
        svg_content = svg_content.replace(
            "<style>", "<defs>\n" + glyph_defs + "\n</defs>\n<style>"
        )

    # Create injector instance
    injector = CornerInjector.from_config(layer_keys, config)

    # Find key groups and inject corner legends
    # Pattern matches key groups with keypos-N class
    key_pattern = re.compile(
        r'(<g[^>]*class="[^"]*keypos-(\d+)[^"]*"[^>]*>)'
        r"(.*?)"
        r"(</g>)",
        re.DOTALL,
    )

    svg_content = key_pattern.sub(injector.inject, svg_content)

    return svg_content
