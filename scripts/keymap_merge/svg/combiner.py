"""SVG stacking and combining utilities."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# SVG namespace constants
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def _register_namespaces() -> None:
    """Register XML namespaces for SVG output."""
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)


def merge_svg_defs(base_root: ET.Element, addition_root: ET.Element) -> None:
    """Merge defs from addition SVG into base SVG.

    Only adds defs with IDs that don't already exist in base.

    Args:
        base_root: Root element of base SVG (will be modified)
        addition_root: Root element of SVG to merge defs from
    """
    base_defs = base_root.find(f"{{{SVG_NS}}}defs")
    addition_defs = addition_root.find(f"{{{SVG_NS}}}defs")

    if addition_defs is None or base_defs is None:
        return

    for child in addition_defs:
        child_id = child.get("id")
        if child_id and base_root.find(f'.//*[@id="{child_id}"]') is None:
            base_defs.append(child)


def append_svg_below(base_path: Path, addition_path: Path) -> None:
    """Append one SVG below another, updating viewBox and dimensions.

    Modifies base_path in place by appending addition_path content below it.

    Args:
        base_path: Path to base SVG (will be modified)
        addition_path: Path to SVG to append below
    """
    _register_namespaces()

    base_tree = ET.parse(base_path)
    addition_tree = ET.parse(addition_path)
    base_root = base_tree.getroot()
    addition_root = addition_tree.getroot()

    # Parse viewBox dimensions
    base_viewbox = [float(x) for x in base_root.get("viewBox", "0 0 0 0").split()]
    add_viewbox = [float(x) for x in addition_root.get("viewBox", "0 0 0 0").split()]

    # Create group with addition content, translated below base
    group = ET.SubElement(base_root, "g", transform=f"translate(0,{base_viewbox[3]})")
    for child in list(addition_root):
        if child.tag != f"{{{SVG_NS}}}defs":
            group.append(child)

    # Merge defs (avoiding duplicates)
    merge_svg_defs(base_root, addition_root)

    # Update viewBox and dimensions
    new_width = max(base_viewbox[2], add_viewbox[2])
    new_height = base_viewbox[3] + add_viewbox[3]
    base_root.set("viewBox", f"{base_viewbox[0]} {base_viewbox[1]} {new_width} {new_height}")
    base_root.set("height", str(new_height))
    base_root.set("width", str(new_width))

    # Write back to file
    base_tree.write(base_path, xml_declaration=False)


def main() -> None:
    """CLI entry point for SVG combining."""
    if len(sys.argv) != 3:
        print("Usage: python -m keymap_merge combine <base.svg> <addition.svg>")
        print("       Appends addition.svg below base.svg (modifies base.svg in place)")
        sys.exit(1)

    base_path = Path(sys.argv[1])
    addition_path = Path(sys.argv[2])

    if not base_path.exists():
        print(f"Error: Base SVG not found: {base_path}", file=sys.stderr)
        sys.exit(1)
    if not addition_path.exists():
        print(f"Error: Addition SVG not found: {addition_path}", file=sys.stderr)
        sys.exit(1)

    append_svg_below(base_path, addition_path)
    print(f"Appended {addition_path.name} below {base_path.name}")


if __name__ == "__main__":
    main()
