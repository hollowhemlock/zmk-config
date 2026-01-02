"""
Keymap layer merging and SVG post-processing utilities.

Designed to work with keymap-drawer output.

Usage:
    python -m keymap_merge merge -i base.yaml --center cmk_dh ...
    python -m keymap_merge inject merged.svg --merged-yaml merged.yaml ...
    python -m keymap_merge combine merged.svg combos.svg
"""

from .config import (
    CornerLayers,
    ThemeColors,
    MergeConfig,
    InjectorConfig,
    load_yaml,
    load_merge_config,
)
from .keymap import load_keymap, get_tap_legend, get_full_legend
from .merger import merge_layers

__all__ = [
    # Config
    "CornerLayers",
    "ThemeColors",
    "MergeConfig",
    "InjectorConfig",
    "load_yaml",
    "load_merge_config",
    # Keymap
    "load_keymap",
    "get_tap_legend",
    "get_full_legend",
    # Merger
    "merge_layers",
]
