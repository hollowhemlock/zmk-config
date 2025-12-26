# Claude Assistant Notes

Tool for parsing and visualizing keyboard keymaps from QMK and ZMK firmware.

### Installation
```bash
pipx install keymap-drawer
```

### Key Capabilities
- Parse QMK and ZMK keymap files
- Generate SVG representations of keyboard layouts
- Support for multiple layers, hold-taps, and combos
- Customizable drawing and parsing configurations
- Web application and command-line interface

### Basic Usage

1. Parse a keymap:
```bash
# For QMK
qmk c2json keymap.c | keymap parse -c 10 -q - > keymap.yaml

# For ZMK
keymap parse -c 10 -z config/cradio.keymap > keymap.yaml
```

2. Draw the keymap:
```bash
keymap draw keymap.yaml > keymap.svg
```

### ZMK-specific features
- `--virtual-layers` flag creates artificial layers for combos
- Example: `keymap parse -z keymap.keymap --virtual-layers Combos` extracts all combos into a "Combos" layer
- Supports parsing individual .dtsi files if they contain complete keymap structure

### Configuration Options
- Customize key representations
- Add SVG glyphs from libraries like Material Design Icons
- Configure drawing styles and layouts
- Support for complex keyboard layouts

### Customizing Combo Labels in config.yaml

**To override a combo's displayed key label**, use `raw_binding_map` with the ZMK binding:
```yaml
raw_binding_map:
  "&kp LT": "( <"
  "&kp GT": ") >"
```

**The `zmk-combos` section** is for display properties (alignment, offset), NOT key legends:
```yaml
zmk-combos:
  combo_cut: { align: bottom, o: 0.15 }  # position adjustments only
```

This is useful for combos that share the same key positions across different layers (e.g., `( )` on main layers vs `< >` on NAV layer).

### Unique Features
- Automated GitHub workflow for generating keymap visualizations
- Support for multiple icon sources
- Flexible parsing of different keyboard firmware formats

### draw/ Directory Structure

```
draw/
├── inputs/                  # Source files (edit directly)
│   ├── config.yaml          # keymap-drawer configuration
│   ├── merge_config.yaml    # merge_layers.py settings (corner_hide, corner_glyph_size)
│   ├── merge_layers.py      # script to merge layers into multi-position diagram
│   ├── append_combos.py     # script to append combo diagrams to merged SVGs
│   └── themes.yaml          # color themes for merged diagram generation
└── outputs/
    ├── keymap_drawer/       # keymap-drawer generated (do not edit)
    │   ├── base.yaml, base.svg
    │   ├── combos_main.yaml, combos_main.svg, combos_main_standalone.svg
    │   └── combos_gaming.yaml, combos_gaming.svg
    └── merged/              # merge_layers.py generated (do not edit)
        ├── merged.yaml, merged.svg (default theme)
        └── merged_<theme>.svg (light, dark, primary, etc.)
```

### Theme System

Themes are defined in `draw/inputs/themes.yaml`. Each theme specifies colors and dark_mode setting:

```yaml
themes:
  light:
    dark_mode: false
    colors:
      tl: "#16C47F"     # Green (top-left / fun layer)
      tr: "#2563EB"     # Blue (top-right / sys layer)
      bl: "#FF9D23"     # Orange (bottom-left / num layer)
      br: "#F93827"     # Red (bottom-right / nav layer)
      text: "#1a1a1a"
      bg: "#ffffff"
      combo_bg: "#ffffff"  # Optional, defaults to bg
```

**Commands:**
```bash
just draw-merged              # Generate default theme (merged.svg)
just draw-merged-all          # Generate all themes (merged_<name>.svg)
just _draw-merged-theme dark  # Generate specific theme
```

**Color order for merge_layers.py:** `tl tr bl br [text] [bg] [combo_bg]`

Position-based naming (tl/tr/bl/br) allows flexibility - corners match layer positions in the merged diagram.

**To color layer activator keys** (Nav, Fun, Sys, Smart-num), set `type: layer-XX` in `draw/inputs/config.yaml`'s `raw_binding_map`:
```yaml
"&sl FUN": { t: Fun, type: layer-tl }
"&mo SYS": { t: Sys, type: layer-tr }
"&smart_num NUM 0": { t: Smart-num, type: layer-bl }
"&sl NAV": { t: Nav, type: layer-br }
```

### References
https://github.com/urob/zmk-config
https://github.com/urob/zmk-helpers
https://github.com/caksoylar/keymap-drawer