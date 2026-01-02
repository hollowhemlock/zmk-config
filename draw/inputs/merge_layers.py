#!/usr/bin/env python3
"""
Backwards-compatible wrapper for keymap_merge package.

This script maintains the original CLI interface for Justfile compatibility.
All logic has been refactored into the keymap_merge package.

Usage (legacy):
    python merge_layers.py -i base.yaml --center cmk_dh -o merged.yaml
    python merge_layers.py --inject-corners merged.svg --merged-yaml merged.yaml

Usage (new):
    python -m keymap_merge merge -i base.yaml --center cmk_dh -o merged.yaml
    python -m keymap_merge inject merged.svg --merged-yaml merged.yaml
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for package import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import yaml

from keymap_merge.config import (
    CornerLayers,
    InjectorConfig,
    ThemeColors,
    colors_from_list,
    load_draw_config,
    load_merge_config,
    load_yaml,
)
from keymap_merge.keymap import load_keymap
from keymap_merge.merger import merge_layers
from keymap_merge.svg.injector import inject_corner_legends


def main():
    """Backwards-compatible CLI entry point."""
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
        default=None,
        help="Padding from top/bottom key edges (default: from config small_pad)"
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
    parser.add_argument(
        "--merge-config",
        type=Path,
        help="Path to merge_config.yaml with corner_hide settings"
    )
    parser.add_argument(
        "--colors",
        nargs='+',
        metavar="COLOR",
        help="Layer colors (4-7 hex values): tl tr bl br [text] [bg] [combo_bg]"
    )

    args = parser.parse_args()

    # Get key dimensions and small_pad from keymap-drawer config
    key_w, key_h, small_pad = 60.0, 56.0, 2.0
    if args.config:
        if args.config.exists():
            config = load_yaml(args.config)
            draw_config = load_draw_config(config)
            key_w, key_h, small_pad = draw_config.key_w, draw_config.key_h, draw_config.small_pad
        else:
            print(f"Warning: Config file not found: {args.config}, using defaults", file=sys.stderr)

    # Use small_pad from config for pad_y if not explicitly set
    pad_y = args.pad_y if args.pad_y is not None else small_pad

    # Load merge config
    merge_cfg = load_merge_config(args.merge_config) if args.merge_config else None
    if merge_cfg is None:
        from keymap_merge.config import MergeConfig
        merge_cfg = MergeConfig()

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

        # Parse colors
        colors = colors_from_list(args.colors) if args.colors else ThemeColors()

        # Build injector config
        injector_config = InjectorConfig(
            key_w=key_w,
            key_h=key_h,
            pad_x=args.pad_x,
            pad_y=pad_y,
            glyph_size=merge_cfg.corner_glyph_size,
            corner_hide=merge_cfg.corner_hide,
            colors=colors,
        )

        svg_content = svg_path.read_text()
        modified = inject_corner_legends(
            svg_content, args.merged_yaml, injector_config, args.glyph_svg
        )
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

    # Build corner layers
    corner_layers = CornerLayers(
        tl=args.tl,
        tr=args.tr,
        bl=args.bl,
        br=args.br,
    )

    # Merge layers
    merged = merge_layers(keymap, args.center, corner_layers, merge_cfg)

    # Write output
    with open(args.output, "w") as f:
        yaml.dump(merged, f, default_flow_style=None, allow_unicode=True, sort_keys=False)

    print(f"Merged keymap written to {args.output}")


if __name__ == "__main__":
    main()
