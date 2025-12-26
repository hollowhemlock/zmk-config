"""Configuration models and loaders for keymap merging."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class CornerLayers(BaseModel):
    """Layer names for each corner position."""

    tl: str | None = Field(None, description="Top-left layer name")
    tr: str | None = Field(None, description="Top-right layer name")
    bl: str | None = Field(None, description="Bottom-left layer name")
    br: str | None = Field(None, description="Bottom-right layer name")


class ThemeColors(BaseModel):
    """Color scheme for corner legends and backgrounds."""

    tl: str = Field("#e5c07b", description="Top-left corner color")
    tr: str = Field("#61afef", description="Top-right corner color")
    bl: str = Field("#98c379", description="Bottom-left corner color")
    br: str = Field("#c678dd", description="Bottom-right corner color")
    text: str = Field("#000000", description="Main text color")
    bg: str = Field("#ffffff", description="Key background color")
    combo_bg: str | None = Field(None, description="Combo background (defaults to bg)")

    def get_combo_bg(self) -> str:
        """Return combo_bg, defaulting to bg if not set."""
        return self.combo_bg if self.combo_bg is not None else self.bg


class MergeConfig(BaseModel):
    """Configuration for layer merging."""

    corner_hide: list[str] = Field(default_factory=list)
    held_key_colors: dict[int, str] = Field(default_factory=dict)
    held_hide: list[str] = Field(default_factory=list)
    corner_glyph_size: int = Field(11, ge=6, le=24)


class DrawConfig(BaseModel):
    """Key dimensions from keymap-drawer config."""

    key_w: float = Field(60.0, ge=20, le=200)
    key_h: float = Field(56.0, ge=20, le=200)
    small_pad: float = Field(2.0, ge=0)


class InjectorConfig(BaseModel):
    """Configuration for SVG corner injection."""

    key_w: float = Field(60.0, ge=20, le=200)
    key_h: float = Field(56.0, ge=20, le=200)
    pad_x: float = Field(10.0, ge=2)
    pad_y: float = Field(2.0, ge=2)
    glyph_size: int = Field(11, ge=6, le=24)
    corner_hide: list[str] = Field(default_factory=list)
    colors: ThemeColors = Field(default_factory=ThemeColors)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_draw_config(config: dict[str, Any]) -> DrawConfig:
    """Extract DrawConfig from keymap-drawer config dict."""
    draw_config = config.get("draw_config", {})
    return DrawConfig(
        key_w=draw_config.get("key_w", 60.0),
        key_h=draw_config.get("key_h", 56.0),
        small_pad=draw_config.get("small_pad", 2.0),
    )


def load_merge_config(path: Path) -> MergeConfig:
    """Load merge configuration from YAML file."""
    if not path.exists():
        return MergeConfig()

    data = load_yaml(path)
    # Convert held_key_colors keys to int (YAML may load as str)
    raw_held = data.get("held_key_colors", {})
    held_key_colors = {int(k): v for k, v in raw_held.items()}

    return MergeConfig(
        corner_hide=data.get("corner_hide", []),
        held_key_colors=held_key_colors,
        held_hide=data.get("held_hide", []),
        corner_glyph_size=data.get("corner_glyph_size", 11),
    )


def colors_from_list(color_args: list[str] | None) -> ThemeColors | None:
    """Parse colors from CLI argument list.

    Args:
        color_args: List of 4-7 hex colors: tl tr bl br [text] [bg] [combo_bg]

    Returns:
        ThemeColors or None if no colors provided
    """
    if not color_args:
        return None

    num_colors = len(color_args)
    if num_colors < 4 or num_colors > 7:
        raise ValueError(f"--colors requires 4-7 values, got {num_colors}")

    bg_color = color_args[5] if num_colors > 5 else "#ffffff"
    return ThemeColors(
        tl=color_args[0],
        tr=color_args[1],
        bl=color_args[2],
        br=color_args[3],
        text=color_args[4] if num_colors > 4 else "#000000",
        bg=bg_color,
        combo_bg=color_args[6] if num_colors > 6 else None,
    )
