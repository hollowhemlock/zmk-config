"""Keymap loading and key legend extraction utilities."""

from pathlib import Path
from typing import Any

import yaml


def load_keymap(path: Path) -> dict[str, Any]:
    """Load keymap YAML file.

    Args:
        path: Path to keymap YAML file (from keymap-drawer parse)

    Returns:
        Keymap data dict with 'layers', 'layout', etc.
    """
    with open(path) as f:
        return yaml.safe_load(f) or {}


def get_tap_legend(key: dict | str | None) -> str:
    """Extract tap-only legend string from a key definition.

    Used for corner layers where we only show the tap value.

    Args:
        key: The key definition (str, dict, or None)

    Returns:
        String tap value for the key
    """
    if key is None:
        return ""
    if isinstance(key, str):
        return key
    if isinstance(key, dict):
        if key.get("type") == "trans":
            return ""
        return key.get("t", key.get("tap", ""))
    return str(key)


def get_full_legend(key: dict | str | None) -> dict[str, Any]:
    """Extract complete legend dict (t/s/h/type) from a key definition.

    Used for the center layer where we preserve all display attributes.

    Args:
        key: The key definition (str, dict, or None)

    Returns:
        Dict with available keys: t, s, h, type
    """
    if key is None:
        return {}
    if isinstance(key, str):
        return {"t": key}
    if isinstance(key, dict):
        if key.get("type") == "trans":
            return {}
        result = {}
        tap = key.get("t", key.get("tap", ""))
        if tap:
            result["t"] = tap
        for field in ("s", "h", "type"):
            if field in key:
                result[field] = key[field]
        return result
    return {"t": str(key)}


def get_layer_keys(layers: dict[str, list], layer_name: str | None, num_keys: int) -> list:
    """Get keys from a layer, with fallback for missing layers.

    Args:
        layers: Dict of layer name -> key list
        layer_name: Layer name to get, or None for empty layer
        num_keys: Expected number of keys (for empty layer generation)

    Returns:
        List of key definitions
    """
    if layer_name is None:
        return [""] * num_keys
    if layer_name not in layers:
        return [""] * num_keys
    return layers[layer_name]
