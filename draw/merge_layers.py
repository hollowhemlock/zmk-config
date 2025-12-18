#!/usr/bin/env python3
"""
Merge multiple keymap layers into a single layer with multi-position legends.

Each key can show up to 7 positions:
- center (t): primary layer tap value
- top-center (s): primary layer shifted value
- bottom-center (h): primary layer hold value (e.g., home row mods)
- top-left (tl): corner layer 1
- top-right (tr): corner layer 2
- bottom-left (bl): corner layer 3
- bottom-right (br): corner layer 4

Position layout:
+---------------------------+
|  tl           s        tr |
|                           |
|            t              |
|                           |
|  bl           h        br |
+---------------------------+
"""

import argparse
import re
import sys
from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    """Load keymap-drawer config YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def get_key_dimensions(config: dict) -> tuple[float, float]:
    """Extract key_w and key_h from config's draw_config section."""
    draw_config = config.get("draw_config", {})
    key_w = draw_config.get("key_w", 60.0)
    key_h = draw_config.get("key_h", 56.0)
    return key_w, key_h


def calculate_corner_offsets(key_w: float = 60, key_h: float = 56, pad_x: float = 10, pad_y: float = 8) -> tuple[int, int]:
    """
    Calculate corner text offsets from key center based on edge padding.

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


def escape_xml(text: str) -> str:
    """Escape XML special characters."""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;"))


def parse_glyph_ref(value: str) -> tuple[str, str] | None:
    """Parse a glyph reference like $$mdi:play-pause$$.

    Returns (source, name) tuple or None if not a glyph reference.
    """
    match = re.match(r'^\$\$([^:]+):([^$]+)\$\$$', value)
    if match:
        return match.group(1), match.group(2)
    return None


def inject_corner_legends(
    svg_content: str,
    merged_yaml_path: Path,
    key_w: float = 60,
    key_h: float = 56,
    pad_x: float = 10,
    pad_y: float = 8,
    glyph_svg_path: Path | None = None
) -> str:
    """Inject corner legend text elements into SVG.

    Reads tl/tr/bl/br values from merged.yaml and adds them as new
    text elements at corner positions within each key group.

    Args:
        svg_content: The SVG content from keymap-drawer
        merged_yaml_path: Path to merged.yaml with tl/tr/bl/br values
        key_w, key_h: Key dimensions
        pad_x, pad_y: Padding from key edges for corner text
        glyph_svg_path: Path to SVG with glyph definitions (e.g., base.svg)

    Returns:
        Modified SVG content with corner legends injected
    """
    # Load merged YAML to get corner values
    with open(merged_yaml_path) as f:
        merged = yaml.safe_load(f)

    # Extract glyph defs from source SVG if provided
    glyph_defs = ""
    if glyph_svg_path and glyph_svg_path.exists():
        source_svg = glyph_svg_path.read_text()
        # Extract glyph SVG elements from defs section
        # Pattern: <svg id="prefix:name">...<svg>...</svg></svg>
        glyph_pattern = re.compile(
            r'<svg id="[^"]+:[^"]+">\s*<svg[^>]*>.*?</svg>\s*</svg>',
            re.DOTALL
        )
        glyphs = glyph_pattern.findall(source_svg)
        if glyphs:
            glyph_defs = "\n".join(glyphs)

    layer_keys = merged.get("layers", {}).get("merged", [])

    # Calculate corner offsets
    x_offset, y_offset = calculate_corner_offsets(key_w, key_h, pad_x, pad_y)
    y_offset_bottom = y_offset + 1  # Adjustment for text-after-edge baseline

    # CSS for corner legend styling
    corner_css = '''
/* Corner legend styles for merged view */
text.tl {
    text-anchor: start;
    dominant-baseline: hanging;
    font-size: 11px;
    fill: #e5c07b;  /* yellow */
}
text.tr {
    text-anchor: end;
    dominant-baseline: hanging;
    font-size: 11px;
    fill: #61afef;  /* blue */
}
text.bl {
    text-anchor: start;
    dominant-baseline: text-after-edge;
    font-size: 11px;
    fill: #98c379;  /* green */
}
text.br {
    text-anchor: end;
    dominant-baseline: text-after-edge;
    font-size: 11px;
    fill: #c678dd;  /* purple */
}
/* Corner glyph/icon colors */
use.tl, .tl path { fill: #e5c07b; }  /* yellow */
use.tr, .tr path { fill: #61afef; }  /* blue */
use.bl, .bl path { fill: #98c379; }  /* green */
use.br, .br path { fill: #c678dd; }  /* purple */
'''

    # Insert CSS before closing </style>
    if '</style>' in svg_content:
        svg_content = svg_content.replace('</style>', corner_css + '</style>')

    # Insert glyph defs if we have them and they're not already present
    if glyph_defs and '<svg id="mdi:' not in svg_content:
        if '<defs>' in svg_content:
            # Insert after existing <defs> tag
            svg_content = re.sub(
                r'(<defs>)',
                r'\1\n' + glyph_defs,
                svg_content
            )
        else:
            # Create <defs> section after opening <svg> tag
            svg_content = re.sub(
                r'(<svg[^>]*>)',
                r'\1\n<defs>\n' + glyph_defs + '\n</defs>',
                svg_content
            )

    # Find key groups and inject corner legends
    # Pattern matches key groups with keypos-N class
    key_pattern = re.compile(
        r'(<g[^>]*class="[^"]*keypos-(\d+)[^"]*"[^>]*>)'
        r'(.*?)'
        r'(</g>)',
        re.DOTALL
    )

    def inject_corners(match):
        opening_tag = match.group(1)
        keypos = int(match.group(2))
        content = match.group(3)
        closing_tag = match.group(4)

        if keypos >= len(layer_keys):
            return match.group(0)

        key = layer_keys[keypos]
        if not isinstance(key, dict):
            return match.group(0)

        # Build corner text elements
        corner_elements = []
        glyph_size = 11  # Size for corner glyphs

        def make_corner_element(value: str, x: int, y: int, css_class: str) -> str:
            """Create a text or use element for a corner legend."""
            glyph = parse_glyph_ref(str(value))
            if glyph:
                source, name = glyph
                glyph_id = f"{source}:{name}"
                # Position glyph - adjust based on corner
                half = glyph_size // 2
                if css_class == "tl":
                    gx, gy = x, y  # top-left: start from corner
                elif css_class == "tr":
                    gx, gy = x - glyph_size, y  # top-right: end at corner
                elif css_class == "bl":
                    gx, gy = x, y - glyph_size  # bottom-left: start from corner
                elif css_class == "br":
                    gx, gy = x - glyph_size, y - glyph_size  # bottom-right
                else:
                    gx, gy = x - half, y - half
                return f'<use href="#{glyph_id}" xlink:href="#{glyph_id}" x="{gx}" y="{gy}" height="{glyph_size}" width="{glyph_size}" class="glyph {css_class}"/>'
            else:
                return f'<text x="{x}" y="{y}" class="{css_class}">{escape_xml(str(value))}</text>'

        if key.get("tl"):
            corner_elements.append(
                make_corner_element(key["tl"], -x_offset, -y_offset, "tl")
            )

        if key.get("tr"):
            corner_elements.append(
                make_corner_element(key["tr"], x_offset, -y_offset, "tr")
            )

        if key.get("bl"):
            corner_elements.append(
                make_corner_element(key["bl"], -x_offset, y_offset_bottom, "bl")
            )

        if key.get("br"):
            corner_elements.append(
                make_corner_element(key["br"], x_offset, y_offset_bottom, "br")
            )

        if not corner_elements:
            return match.group(0)

        new_content = content + "\n" + "\n".join(corner_elements)
        return opening_tag + new_content + closing_tag

    svg_content = key_pattern.sub(inject_corners, svg_content)

    return svg_content


def load_keymap(path: Path) -> dict:
    """Load keymap YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def get_key_legend(key, extract_full: bool = False) -> str | dict:
    """Extract the display legend(s) from a key definition.

    Args:
        key: The key definition (str, dict, or None)
        extract_full: If True, return dict with t/s/h; if False, return tap string only

    Returns:
        If extract_full=False: string tap value
        If extract_full=True: dict with {t: ..., s: ..., h: ...}
    """
    if key is None:
        return {} if extract_full else ""
    if isinstance(key, str):
        return {"t": key} if extract_full else key
    if isinstance(key, dict):
        # Skip transparent keys
        if key.get("type") == "trans":
            return {} if extract_full else ""
        if extract_full:
            result = {}
            tap = key.get("t", key.get("tap", ""))
            if tap:
                result["t"] = tap
            if "s" in key:
                result["s"] = key["s"]
            if "h" in key:
                result["h"] = key["h"]
            if "type" in key:
                result["type"] = key["type"]
            return result
        # Return tap value if it exists
        return key.get("t", key.get("tap", ""))
    return {"t": str(key)} if extract_full else str(key)


def merge_layers(
    keymap: dict,
    center_layer: str,
    tl_layer: str | None = None,
    tr_layer: str | None = None,
    bl_layer: str | None = None,
    br_layer: str | None = None,
) -> dict:
    """Merge multiple layers into a single layer with multi-position legends.

    Output positions:
    - t, s, h: from center layer (preserved)
    - tl, tr, bl, br: from corner layers (tap values only)
    """
    layers = keymap.get("layers", {})

    # Validate center layer exists
    if center_layer not in layers:
        print(f"Error: Center layer '{center_layer}' not found in keymap", file=sys.stderr)
        print(f"Available layers: {list(layers.keys())}", file=sys.stderr)
        sys.exit(1)

    center_keys = layers[center_layer]
    num_keys = len(center_keys)

    # Get keys from other layers (or empty lists if not specified)
    def get_layer_keys(layer_name: str | None) -> list:
        if layer_name is None:
            return [""] * num_keys
        if layer_name not in layers:
            print(f"Warning: Layer '{layer_name}' not found, using empty", file=sys.stderr)
            return [""] * num_keys
        return layers[layer_name]

    tl_keys = get_layer_keys(tl_layer)
    tr_keys = get_layer_keys(tr_layer)
    bl_keys = get_layer_keys(bl_layer)
    br_keys = get_layer_keys(br_layer)

    # Build merged layer
    merged_keys = []
    for i in range(num_keys):
        # Get full key definition from center layer (preserves t, s, h)
        center_full = get_key_legend(center_keys[i], extract_full=True)

        # Get tap values from corner layers
        tl = get_key_legend(tl_keys[i]) if i < len(tl_keys) else ""
        tr = get_key_legend(tr_keys[i]) if i < len(tr_keys) else ""
        bl = get_key_legend(bl_keys[i]) if i < len(bl_keys) else ""
        br = get_key_legend(br_keys[i]) if i < len(br_keys) else ""

        # Build key definition with non-empty positions
        key_def = {}

        # Center positions (from center layer)
        if center_full.get("t"):
            key_def["t"] = center_full["t"]
        if center_full.get("s"):
            key_def["s"] = center_full["s"]
        if center_full.get("h"):
            key_def["h"] = center_full["h"]
        if center_full.get("type"):
            key_def["type"] = center_full["type"]

        # Corner positions (from corner layers) - custom keys for injection
        if tl:
            key_def["tl"] = tl
        if tr:
            key_def["tr"] = tr
        if bl:
            key_def["bl"] = bl
        if br:
            key_def["br"] = br

        # Simplify to string if only center tap value
        if len(key_def) == 1 and "t" in key_def:
            merged_keys.append(key_def["t"])
        elif len(key_def) == 0:
            merged_keys.append("")
        else:
            merged_keys.append(key_def)

    # Create output keymap with single merged layer
    output = {
        "layout": keymap.get("layout", {}),
        "layers": {
            "merged": merged_keys
        }
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple keymap layers into a single multi-position legend layer"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        help="Input keymap YAML file (from keymap-drawer parse)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output merged YAML file"
    )
    parser.add_argument(
        "--center",
        help="Layer name for center position (required for merge)"
    )
    parser.add_argument(
        "--tl",
        help="Layer name for top-left corner position"
    )
    parser.add_argument(
        "--tr",
        help="Layer name for top-right corner position"
    )
    parser.add_argument(
        "--bl",
        help="Layer name for bottom-left corner position"
    )
    parser.add_argument(
        "--br",
        help="Layer name for bottom-right corner position"
    )
    parser.add_argument(
        "--list-layers",
        action="store_true",
        help="List available layers and exit"
    )
    parser.add_argument(
        "--inject-corners",
        type=Path,
        metavar="SVG_FILE",
        help="Post-process SVG to inject corner legends from merged YAML"
    )
    parser.add_argument(
        "--merged-yaml",
        type=Path,
        help="Path to merged.yaml (required with --inject-corners)"
    )
    parser.add_argument(
        "--pad-x",
        type=float,
        default=10,
        help="Padding from left/right key edges (default: 10)"
    )
    parser.add_argument(
        "--pad-y",
        type=float,
        default=8,
        help="Padding from top/bottom key edges (default: 8)"
    )
    parser.add_argument(
        "-c", "--config",
        type=Path,
        help="Path to keymap-drawer config.yaml (reads key_w and key_h from draw_config)"
    )
    parser.add_argument(
        "--glyph-svg",
        type=Path,
        help="Path to SVG with glyph definitions to copy (e.g., base.svg)"
    )

    args = parser.parse_args()

    # Get key dimensions from config or use defaults
    key_w, key_h = 60.0, 56.0
    if args.config:
        if args.config.exists():
            config = load_config(args.config)
            key_w, key_h = get_key_dimensions(config)
        else:
            print(f"Warning: Config file not found: {args.config}, using defaults", file=sys.stderr)

    # SVG corner injection mode
    if args.inject_corners:
        svg_path = args.inject_corners
        if not svg_path.exists():
            print(f"Error: SVG file not found: {svg_path}", file=sys.stderr)
            sys.exit(1)
        if not args.merged_yaml:
            parser.error("--merged-yaml is required with --inject-corners")
        if not args.merged_yaml.exists():
            print(f"Error: Merged YAML file not found: {args.merged_yaml}", file=sys.stderr)
            sys.exit(1)

        svg_content = svg_path.read_text()
        modified = inject_corner_legends(svg_content, args.merged_yaml, key_w, key_h, args.pad_x, args.pad_y, args.glyph_svg)
        svg_path.write_text(modified)
        print(f"Injected corner legends into {svg_path}")
        sys.exit(0)

    # Require input for other operations
    if not args.input:
        parser.error("--input is required")

    # Load input keymap
    keymap = load_keymap(args.input)

    # List layers mode
    if args.list_layers:
        layers = keymap.get("layers", {})
        print("Available layers:")
        for name in layers.keys():
            print(f"  - {name}")
        sys.exit(0)

    # Validate required args for merge
    if not args.center:
        parser.error("--center is required for merge operation")
    if not args.output:
        parser.error("--output is required for merge operation")

    # Merge layers
    merged = merge_layers(
        keymap,
        center_layer=args.center,
        tl_layer=args.tl,
        tr_layer=args.tr,
        bl_layer=args.bl,
        br_layer=args.br,
    )

    # Write output
    with open(args.output, "w") as f:
        yaml.dump(merged, f, default_flow_style=None, allow_unicode=True, sort_keys=False)

    print(f"Merged keymap written to {args.output}")


if __name__ == "__main__":
    main()
