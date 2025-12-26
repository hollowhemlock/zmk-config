"""Layer merging logic for combining multiple keymap layers into one."""

import sys
from typing import Any

from .config import CornerLayers, MergeConfig
from .keymap import get_tap_legend, get_full_legend, get_layer_keys


def merge_layers(
    keymap: dict[str, Any],
    center_layer: str,
    corner_layers: CornerLayers,
    merge_config: MergeConfig,
) -> dict[str, Any]:
    """Merge multiple layers into a single layer with multi-position legends.

    Output positions:
    - t, s, h: from center layer (preserved)
    - tl, tr, bl, br: from corner layers (tap values only)

    Args:
        keymap: Full keymap dict with 'layers' key
        center_layer: Layer name for center position (primary layer)
        corner_layers: CornerLayers specifying tl/tr/bl/br layer names
        merge_config: MergeConfig with hide settings and held key colors

    Returns:
        New keymap dict with single 'merged' layer
    """
    layers = keymap.get("layers", {})

    # Validate center layer exists
    if center_layer not in layers:
        print(f"Error: Center layer '{center_layer}' not found in keymap", file=sys.stderr)
        print(f"Available layers: {list(layers.keys())}", file=sys.stderr)
        sys.exit(1)

    center_keys = layers[center_layer]
    num_keys = len(center_keys)

    # Get keys from corner layers
    tl_keys = get_layer_keys(layers, corner_layers.tl, num_keys)
    tr_keys = get_layer_keys(layers, corner_layers.tr, num_keys)
    bl_keys = get_layer_keys(layers, corner_layers.bl, num_keys)
    br_keys = get_layer_keys(layers, corner_layers.br, num_keys)

    # Build merged layer
    merged_keys = []
    for i in range(num_keys):
        key_def = _merge_key(
            i,
            center_keys[i],
            tl_keys[i] if i < len(tl_keys) else "",
            tr_keys[i] if i < len(tr_keys) else "",
            bl_keys[i] if i < len(bl_keys) else "",
            br_keys[i] if i < len(br_keys) else "",
            merge_config,
        )
        merged_keys.append(key_def)

    # Create output keymap with single merged layer
    return {
        "layout": keymap.get("layout", {}),
        "layers": {"merged": merged_keys},
    }


def _merge_key(
    key_index: int,
    center_key: Any,
    tl_key: Any,
    tr_key: Any,
    bl_key: Any,
    br_key: Any,
    merge_config: MergeConfig,
) -> dict | str:
    """Merge a single key from multiple layers.

    Args:
        key_index: Position index of the key
        center_key: Key definition from center layer
        tl_key, tr_key, bl_key, br_key: Key definitions from corner layers
        merge_config: Configuration for hiding and held keys

    Returns:
        Merged key definition (dict or string if simple)
    """
    # Get full definition from center layer (preserves t, s, h, type)
    center_full = get_full_legend(center_key)

    # Get tap values from corner layers
    tl = get_tap_legend(tl_key)
    tr = get_tap_legend(tr_key)
    bl = get_tap_legend(bl_key)
    br = get_tap_legend(br_key)

    # Build key definition with non-empty positions
    key_def: dict[str, Any] = {}

    # Center positions (from center layer)
    if center_full.get("t"):
        key_def["t"] = center_full["t"]
    if center_full.get("s"):
        key_def["s"] = center_full["s"]
    if center_full.get("h"):
        key_def["h"] = center_full["h"]
    if center_full.get("type"):
        key_def["type"] = center_full["type"]

    # Override type to "held-{corner}" for specified key positions (layer activators)
    held_hide_set = set(merge_config.held_hide)
    if key_index in merge_config.held_key_colors:
        key_def["type"] = f"held-{merge_config.held_key_colors[key_index]}"
        # Hide specified values on held keys
        if key_def.get("s") in held_hide_set:
            del key_def["s"]
        if key_def.get("h") in held_hide_set:
            del key_def["h"]

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
        return key_def["t"]
    if len(key_def) == 0:
        return ""

    return key_def
