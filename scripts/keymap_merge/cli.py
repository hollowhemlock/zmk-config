"""Command-line interface for keymap merging utilities."""

import argparse
import sys
from pathlib import Path

import yaml

from .config import (
    CornerLayers,
    InjectorConfig,
    ThemeColors,
    colors_from_list,
    load_draw_config,
    load_merge_config,
    load_yaml,
)
from .keymap import load_keymap
from .merger import merge_layers
from .svg.combiner import append_svg_below
from .svg.injector import inject_corner_legends


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="keymap_merge",
        description="Keymap layer merging and SVG post-processing utilities",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- merge subcommand ---
    merge_parser = subparsers.add_parser(
        "merge",
        help="Merge multiple layers into a single multi-position legend layer",
    )
    merge_parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Input keymap YAML file (from keymap-drawer parse)",
    )
    merge_parser.add_argument(
        "-o", "--output",
        type=Path,
        required=True,
        help="Output merged YAML file",
    )
    merge_parser.add_argument(
        "--center",
        required=True,
        help="Layer name for center position",
    )
    merge_parser.add_argument("--tl", help="Layer name for top-left corner")
    merge_parser.add_argument("--tr", help="Layer name for top-right corner")
    merge_parser.add_argument("--bl", help="Layer name for bottom-left corner")
    merge_parser.add_argument("--br", help="Layer name for bottom-right corner")
    merge_parser.add_argument(
        "--merge-config",
        type=Path,
        help="Path to merge_config.yaml with corner_hide settings",
    )
    merge_parser.add_argument(
        "--list-layers",
        action="store_true",
        help="List available layers and exit",
    )

    # --- inject subcommand ---
    inject_parser = subparsers.add_parser(
        "inject",
        help="Inject corner legends into SVG from merged YAML",
    )
    inject_parser.add_argument(
        "svg_file",
        type=Path,
        help="SVG file to modify (in place)",
    )
    inject_parser.add_argument(
        "--merged-yaml",
        type=Path,
        required=True,
        help="Path to merged.yaml with tl/tr/bl/br values",
    )
    inject_parser.add_argument(
        "-c", "--config",
        type=Path,
        help="Path to keymap-drawer config.yaml (reads key_w and key_h)",
    )
    inject_parser.add_argument(
        "--merge-config",
        type=Path,
        help="Path to merge_config.yaml with corner_hide settings",
    )
    inject_parser.add_argument(
        "--glyph-svg",
        type=Path,
        help="Path to SVG with glyph definitions to copy (e.g., base.svg)",
    )
    inject_parser.add_argument(
        "--pad-x",
        type=float,
        default=10,
        help="Padding from left/right key edges (default: 10)",
    )
    inject_parser.add_argument(
        "--pad-y",
        type=float,
        default=None,
        help="Padding from top/bottom key edges (default: from config small_pad)",
    )
    inject_parser.add_argument(
        "--colors",
        nargs="+",
        metavar="COLOR",
        help="Layer colors (4-7 hex values): tl tr bl br [text] [bg] [combo_bg]",
    )

    # --- combine subcommand ---
    combine_parser = subparsers.add_parser(
        "combine",
        help="Append one SVG below another",
    )
    combine_parser.add_argument(
        "base_svg",
        type=Path,
        help="Base SVG file (will be modified in place)",
    )
    combine_parser.add_argument(
        "addition_svg",
        type=Path,
        help="SVG to append below the base",
    )

    return parser


def cmd_merge(args: argparse.Namespace) -> int:
    """Execute merge subcommand."""
    # Load input keymap
    keymap = load_keymap(args.input)

    # List layers mode
    if args.list_layers:
        layers = keymap.get("layers", {})
        print("Available layers:")
        for name in layers.keys():
            print(f"  - {name}")
        return 0

    # Load merge config
    merge_config = load_merge_config(args.merge_config) if args.merge_config else None
    if merge_config is None:
        from .config import MergeConfig
        merge_config = MergeConfig()

    # Build corner layers
    corner_layers = CornerLayers(
        tl=args.tl,
        tr=args.tr,
        bl=args.bl,
        br=args.br,
    )

    # Merge layers
    merged = merge_layers(keymap, args.center, corner_layers, merge_config)

    # Write output
    with open(args.output, "w") as f:
        yaml.dump(merged, f, default_flow_style=None, allow_unicode=True, sort_keys=False)

    print(f"Merged keymap written to {args.output}")
    return 0


def cmd_inject(args: argparse.Namespace) -> int:
    """Execute inject subcommand."""
    if not args.svg_file.exists():
        print(f"Error: SVG file not found: {args.svg_file}", file=sys.stderr)
        return 1
    if not args.merged_yaml.exists():
        print(f"Error: Merged YAML file not found: {args.merged_yaml}", file=sys.stderr)
        return 1

    # Load keymap-drawer config for key dimensions
    key_w, key_h, small_pad = 60.0, 56.0, 2.0
    if args.config and args.config.exists():
        config = load_yaml(args.config)
        draw_config = load_draw_config(config)
        key_w, key_h, small_pad = draw_config.key_w, draw_config.key_h, draw_config.small_pad

    # Use small_pad from config for pad_y if not explicitly set
    pad_y = args.pad_y if args.pad_y is not None else small_pad

    # Load merge config for corner_hide and glyph_size
    glyph_size = 11
    corner_hide: list[str] = []
    if args.merge_config and args.merge_config.exists():
        merge_cfg = load_merge_config(args.merge_config)
        corner_hide = merge_cfg.corner_hide
        glyph_size = merge_cfg.corner_glyph_size

    # Parse colors from CLI args or use defaults
    colors = colors_from_list(args.colors) if args.colors else ThemeColors()

    # Build injector config
    injector_config = InjectorConfig(
        key_w=key_w,
        key_h=key_h,
        pad_x=args.pad_x,
        pad_y=pad_y,
        glyph_size=glyph_size,
        corner_hide=corner_hide,
        colors=colors,
    )

    # Read, inject, write
    svg_content = args.svg_file.read_text()
    modified = inject_corner_legends(
        svg_content, args.merged_yaml, injector_config, args.glyph_svg
    )
    args.svg_file.write_text(modified)

    print(f"Injected corner legends into {args.svg_file}")
    return 0


def cmd_combine(args: argparse.Namespace) -> int:
    """Execute combine subcommand."""
    if not args.base_svg.exists():
        print(f"Error: Base SVG not found: {args.base_svg}", file=sys.stderr)
        return 1
    if not args.addition_svg.exists():
        print(f"Error: Addition SVG not found: {args.addition_svg}", file=sys.stderr)
        return 1

    append_svg_below(args.base_svg, args.addition_svg)
    print(f"Appended {args.addition_svg.name} below {args.base_svg.name}")
    return 0


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "merge":
        sys.exit(cmd_merge(args))
    elif args.command == "inject":
        sys.exit(cmd_inject(args))
    elif args.command == "combine":
        sys.exit(cmd_combine(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
