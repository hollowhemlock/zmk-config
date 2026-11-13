#!/usr/bin/env python3
"""Write a merged-diagram config with a named theme to stdout (requires PyYAML)."""

import argparse
import html
from pathlib import Path

import yaml


def luminance(color):
    """WCAG relative luminance of a six-digit RGB color."""
    rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def theme_config(config, theme):
    colors = theme['colors']
    typography = theme.get('typography', {})
    bg, text = colors['bg'], colors['text']
    css = [
        '/* Named merged theme overrides */',
        f'svg.keymap {{ background-color: {bg}; fill: {text}; }}',
        f'rect.key {{ fill: {bg}; }}',
        f'rect.combo, rect.combo-separate {{ fill: {colors.get("combo_bg", bg)}; }}',
        f'text, use {{ fill: {text}; }}',
        f'text.label, text.footer {{ stroke: {bg}; }}',
    ]
    if 'border' in colors:
        css.append(f'rect.key, rect.combo, rect.combo-separate {{ stroke: {colors["border"]}; }}')
    activators = []
    for corner in ('tl', 'tr', 'bl', 'br'):
        color = colors[corner]
        light = luminance(color)
        foreground = '#000000' if (light + 0.05) / 0.05 >= 1.05 / (light + 0.05) else '#FFFFFF'
        css.extend([
            f'text.{corner}, use.{corner} {{ fill: {color}; }}',
            f'text.{corner} {{ font-size: {typography.get("corner_size", "8px")}; '
            f'font-weight: {typography.get("corner_weight", 400)}; }}',
        ])
        activators.extend([
            f'.held-{corner} rect, .layer-{corner} rect {{ fill: {color}; }}',
            f'.held-{corner} text, .layer-{corner} text, '
            f'.held-{corner} use, .layer-{corner} use {{ fill: {foreground}; }}',
        ])
    css.extend(activators)
    draw = config.setdefault('draw_config', {})
    draw['dark_mode'] = theme.get('dark_mode', False)
    draw['svg_extra_style'] = draw.get('svg_extra_style', '') + '\n' + '\n'.join(css) + '\n'
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('themes', type=Path)
    parser.add_argument('theme')
    parser.add_argument('--svg', type=Path, help='add an explicit background to a rendered SVG instead')
    args = parser.parse_args()
    themes = yaml.safe_load(args.themes.read_text())['themes']
    if args.theme not in themes:
        parser.error(f'unknown theme {args.theme!r}; choose from: {", ".join(themes)}')
    if args.svg:
        # Keep renderer output intact; the root opening tag precedes all artwork.
        svg = args.svg.read_text()
        end = svg.index('>', svg.index('<svg')) + 1
        bg = html.escape(themes[args.theme]['colors']['bg'], quote=True)
        rect = f'\n<rect width="100%" height="100%" fill="{bg}" class="diagram-background"/>'
        args.svg.write_text(svg[:end] + rect + svg[end:])
        return
    config = yaml.safe_load(args.config.read_text())
    print(yaml.safe_dump(theme_config(config, themes[args.theme]), sort_keys=False), end='')


if __name__ == '__main__':
    main()
