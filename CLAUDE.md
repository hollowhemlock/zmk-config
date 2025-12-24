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

### draw/ Directory Files

**Source files (edit directly):**
- `config.yaml` - keymap-drawer configuration
- `merge_config.yaml` - merge_layers.py settings (corner_hide, held_keys)
- `merge_layers.py` - script to merge layers into multi-position diagram

**Generated files (do not edit directly):**
- `base.yaml`, `base.svg` - parsed from config/base.keymap
- `combos_main.yaml`, `combos_main.svg` - main layer combos
- `combos_gaming.yaml`, `combos_gaming.svg` - gaming layer combos
- `merged.yaml`, `merged.svg` - merged multi-position diagram

### References
https://github.com/urob/zmk-config
https://github.com/urob/zmk-helpers
https://github.com/caksoylar/keymap-drawer