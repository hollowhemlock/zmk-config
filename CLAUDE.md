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

### ZMK Combo Gotchas

**Duplicate combo names fail silently.** Later definitions override earlier ones with no warning. Run `just check` before building to detect duplicates.

**Layer priority matters.** Higher numbered layers win when multiple layers are active. If using `&mo SYS` from a gaming layer, SYS must have a higher layer number than gaming layers:
```c
// WRONG: SYS (5) < GAM (6) - gaming layer keys will override SYS
#define SYS 5
#define GAM 6

// CORRECT: SYS (8) > GAM (5) - SYS overlays gaming layers
#define GAM 5
#define SYS 8
```

**`require-prior-idle-ms` blocks combos during active typing.** Defined via `COMBO_HOOK` in zmk-helpers:
```c
#define COMBO_HOOK require-prior-idle-ms = <100>;
ZMK_COMBO(my_combo, ...)  // Won't trigger if any key pressed in last 100ms
```
Disable for combos that must work anytime (like layer access during gaming):
```c
#undef COMBO_HOOK
#define COMBO_HOOK
ZMK_COMBO(sys_gam, &mo SYS, RT0 RT1, GAM, 50)  // No idle restriction
```

### Build Commands

```bash
just check          # Check for duplicate combos + layer priority (runs before build)
just build cradio   # Build firmware for cradio
just build all      # Build all targets
just draw           # Generate keymap diagrams
just release cradio # Build + draw + copy artifacts
```

### Directory Structure

```
scripts/
├── checks/
│   ├── check_combos.sh      # Duplicate combo name checker
│   └── check_layers.sh      # Layer priority checker (SYS highest)
└── zmk_format.py            # ZMK keymap formatter

draw/
├── inputs/                  # Source files (edit directly)
│   ├── config.yaml          # keymap-drawer configuration
│   └── themes.yaml          # color themes for merged diagram generation
└── outputs/
    ├── keymap_drawer/       # keymap-drawer generated (do not edit)
    │   └── base.yaml, base.svg
    └── merged/              # keymap stack-layers generated (do not edit)
        ├── merged.yaml, merged.svg (default theme)
        ├── merged_<theme>.svg (light, dark, primary, etc.)
        └── merged_gaming.yaml, merged_gaming.svg
```

### Theme System

Themes are defined in `draw/inputs/themes.yaml`. Each theme specifies colors and dark_mode setting:

```yaml
themes:
  light:
    dark_mode: false
    colors:
      tl: "#F93827"     # Red (top-left / fun layer)
      tr: "#2563EB"     # Blue (top-right / sys layer)
      bl: "#16A34A"     # Green (bottom-left / num layer)
      br: "#FF9D23"     # Orange (bottom-right / nav layer)
      text: "#1a1a1a"
      bg: "#ffffff"
      combo_bg: "#ffffff"  # Optional, defaults to bg
```

**Commands:**
```bash
just draw-merged              # Generate default theme (merged.svg)
just draw-merged-all          # Generate all themes (merged_<name>.svg)
just draw-merged-gaming       # Generate gaming merged diagram (merged_gaming.svg)
just _draw-merged-theme dark  # Generate specific theme
```

**Color order for --colors arg:** `tl tr bl br [text] [bg] [combo_bg]`

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