#!/usr/bin/env python3
"""
Merge multiple keymap layers into a single layer with multi-position legends.

Each key position shows bindings from up to 5 layers:
- center (t): primary layer
- top-left (s/shifted): second layer
- top-right (h/hold): third layer
- bottom-left (left): fourth layer
- bottom-right (right): fifth layer
"""

import argparse
import re
import sys
from pathlib import Path

import yaml


def move_legends_to_corners(svg_content: str) -> str:
    """
    Post-process SVG to move legend text to corners.

    Original positions (relative to key center):
    - shifted: x=0, y=-24 (top center)
    - hold: x=0, y=24 (bottom center)
    - left: x=-24, y=0 (left center)
    - right: x=24, y=0 (right center)

    New corner positions:
    - shifted -> top-left: x=-22, y=-18
    - hold -> top-right: x=22, y=-18
    - left -> bottom-left: x=-22, y=20
    - right -> bottom-right: x=22, y=20
    """
    # Update CSS for text anchoring
    css_updates = '''
/* Corner positioning for merged layer view */
text.shifted {
    text-anchor: start;
    dominant-baseline: hanging;
}
text.hold {
    text-anchor: end;
    dominant-baseline: hanging;
}
text.left {
    text-anchor: start;
    dominant-baseline: auto;
}
text.right {
    text-anchor: end;
    dominant-baseline: auto;
}
'''

    # Insert custom CSS before closing </style> or </defs>
    if '</style>' in svg_content:
        svg_content = svg_content.replace('</style>', css_updates + '</style>')

    # Update shifted: y=-24 -> y=-18, x=0 -> x=-22
    svg_content = re.sub(
        r'(<text x=")0(" y=")-24(" class="[^"]*shifted)',
        r'\g<1>-22\g<2>-18\g<3>',
        svg_content
    )

    # Update hold: y=24 -> y=-18, x=0 -> x=22
    svg_content = re.sub(
        r'(<text x=")0(" y=")24(" class="[^"]*hold)',
        r'\g<1>22\g<2>-18\g<3>',
        svg_content
    )

    # Update left: x=-24 -> x=-22, y=0 -> y=20
    svg_content = re.sub(
        r'(<text x=")-24(" y=")0(" class="[^"]*left)',
        r'\g<1>-22\g<2>20\g<3>',
        svg_content
    )

    # Update right: x=24 -> x=22, y=0 -> y=20
    svg_content = re.sub(
        r'(<text x=")24(" y=")0(" class="[^"]*right)',
        r'\g<1>22\g<2>20\g<3>',
        svg_content
    )

    return svg_content


def load_keymap(path: Path) -> dict:
    """Load keymap YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def get_key_legend(key) -> str:
    """Extract the display legend from a key definition."""
    if key is None:
        return ""
    if isinstance(key, str):
        return key
    if isinstance(key, dict):
        # Skip transparent keys
        if key.get("type") == "trans":
            return ""
        # Return tap value if it exists
        return key.get("t", key.get("tap", ""))
    return str(key)


def merge_layers(
    keymap: dict,
    center_layer: str,
    top_layer: str | None = None,
    bottom_layer: str | None = None,
    left_layer: str | None = None,
    right_layer: str | None = None,
) -> dict:
    """Merge multiple layers into a single layer with multi-position legends."""
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

    top_keys = get_layer_keys(top_layer)
    bottom_keys = get_layer_keys(bottom_layer)
    left_keys = get_layer_keys(left_layer)
    right_keys = get_layer_keys(right_layer)

    # Build merged layer
    merged_keys = []
    for i in range(num_keys):
        center = get_key_legend(center_keys[i])
        top = get_key_legend(top_keys[i]) if i < len(top_keys) else ""
        bottom = get_key_legend(bottom_keys[i]) if i < len(bottom_keys) else ""
        left = get_key_legend(left_keys[i]) if i < len(left_keys) else ""
        right = get_key_legend(right_keys[i]) if i < len(right_keys) else ""

        # Build key definition with non-empty positions
        key_def = {}
        if center:
            key_def["t"] = center
        if top:
            key_def["s"] = top
        if bottom:
            key_def["h"] = bottom
        if left:
            key_def["left"] = left
        if right:
            key_def["right"] = right

        # Simplify to string if only center value
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
        "--top",
        help="Layer name for top position"
    )
    parser.add_argument(
        "--bottom",
        help="Layer name for bottom position"
    )
    parser.add_argument(
        "--left",
        help="Layer name for left position"
    )
    parser.add_argument(
        "--right",
        help="Layer name for right position"
    )
    parser.add_argument(
        "--list-layers",
        action="store_true",
        help="List available layers and exit"
    )
    parser.add_argument(
        "--corners",
        type=Path,
        metavar="SVG_FILE",
        help="Post-process an SVG file to move legends to corners"
    )

    args = parser.parse_args()

    # SVG corner post-processing mode
    if args.corners:
        svg_path = args.corners
        if not svg_path.exists():
            print(f"Error: SVG file not found: {svg_path}", file=sys.stderr)
            sys.exit(1)

        svg_content = svg_path.read_text()
        modified = move_legends_to_corners(svg_content)
        svg_path.write_text(modified)
        print(f"Moved legends to corners in {svg_path}")
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
        top_layer=args.top,
        bottom_layer=args.bottom,
        left_layer=args.left,
        right_layer=args.right,
    )

    # Write output
    with open(args.output, "w") as f:
        yaml.dump(merged, f, default_flow_style=None, allow_unicode=True, sort_keys=False)

    print(f"Merged keymap written to {args.output}")


if __name__ == "__main__":
    main()
