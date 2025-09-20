# Claude Assistant Notes

## keymap-drawer

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

### Unique Features
- Automated GitHub workflow for generating keymap visualizations
- Support for multiple icon sources
- Flexible parsing of different keyboard firmware formats

Documentation: https://github.com/caksoylar/keymap-drawer/blob/main/README.md