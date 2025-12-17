# Keymap SVG Stacker - TODO List

A Python tool to combine multiple keymap-drawer SVG layer outputs into a single stacked/composite image.

## Research & Setup

- [ ] Research Python SVG manipulation libraries:
  - [ ] `svgutils` - lightweight, good for composing SVGs
  - [ ] `svgwrite` - creating SVGs from scratch
  - [ ] `cairosvg` - SVG to PNG/PDF conversion
  - [ ] `lxml` - XML/SVG parsing and manipulation
  - [ ] `svgelements` - parsing and manipulating SVG paths
- [ ] Decide on primary library (recommendation: `svgutils` + `cairosvg`)
- [ ] Set up Python virtual environment
- [ ] Create `requirements.txt` with dependencies

## Core Functionality

### 1. SVG Parsing
- [ ] Load individual layer SVGs from keymap-drawer output
- [ ] Extract viewBox dimensions from each SVG
- [ ] Parse layer name/title from SVG (if present)
- [ ] Handle different SVG sizes gracefully

### 2. Layout Options
- [ ] **Vertical stack** - layers stacked top to bottom
- [ ] **Horizontal stack** - layers side by side
- [ ] **Grid layout** - N columns x M rows
- [ ] **Single layer with overlays** - base layer + combo/hold info overlaid
- [ ] Configurable padding/margins between layers
- [ ] Configurable spacing and alignment

### 3. SVG Composition
- [ ] Calculate total canvas size based on layout
- [ ] Position each layer SVG at correct coordinates
- [ ] Preserve styles and CSS from original SVGs
- [ ] Merge/deduplicate common CSS definitions
- [ ] Add optional layer labels/titles
- [ ] Add optional background color/rectangle

### 4. Output Options
- [ ] Output combined SVG
- [ ] Convert to PNG (using cairosvg)
- [ ] Convert to PDF (using cairosvg)
- [ ] Configurable output resolution/scale for raster formats

## CLI Interface

- [ ] Create CLI using `argparse` or `click`
- [ ] Arguments to support:
  ```
  --input, -i       Input SVG files (multiple) or glob pattern
  --output, -o      Output filename
  --layout          vertical|horizontal|grid
  --columns         Number of columns for grid layout
  --padding         Padding between layers (px)
  --margin          Outer margin (px)
  --labels          Add layer name labels (bool)
  --label-position  top|bottom|left|right
  --background      Background color (hex or name)
  --scale           Output scale factor
  --format          svg|png|pdf
  ```

## Example Usage

```bash
# Stack all layers vertically
python keymap_stacker.py -i layers/*.svg -o keymap_full.svg --layout vertical

# Create 2-column grid
python keymap_stacker.py -i base.svg nav.svg num.svg sym.svg -o keymap.png --layout grid --columns 2

# Single layer with custom styling
python keymap_stacker.py -i base.svg -o base_styled.svg --background "#ffffff" --margin 20
```

## Integration with keymap-drawer

- [ ] Option to run keymap-drawer parse + draw automatically
- [ ] Accept keymap.yaml as input and generate per-layer SVGs
- [ ] Config file support (YAML) for persistent settings
- [ ] Match keymap-drawer's styling/fonts

## Advanced Features (Nice to Have)

- [ ] Layer transparency/opacity control
- [ ] Selective combo overlay on base layer only
- [ ] Custom CSS injection
- [ ] Layer reordering
- [ ] Layer filtering (include/exclude specific layers)
- [ ] Title/header text for the combined image
- [ ] Legend generation
- [ ] Dark mode / theme support
- [ ] Watch mode for auto-regeneration

## Project Structure

```
keymap-svg-stacker/
├── keymap_stacker/
│   ├── __init__.py
│   ├── cli.py           # CLI entry point
│   ├── parser.py        # SVG parsing utilities
│   ├── composer.py      # SVG composition logic
│   ├── converter.py     # PNG/PDF conversion
│   └── config.py        # Configuration handling
├── tests/
│   ├── test_parser.py
│   ├── test_composer.py
│   └── fixtures/        # Sample SVG files
├── examples/
│   └── example_config.yaml
├── requirements.txt
├── setup.py
└── README.md
```

## Dependencies

```txt
# requirements.txt
svgutils>=0.3.4
cairosvg>=2.7.0
lxml>=4.9.0
click>=8.0.0
pyyaml>=6.0
```

## Testing

- [ ] Unit tests for SVG parsing
- [ ] Unit tests for layout calculations
- [ ] Integration tests with real keymap-drawer output
- [ ] Test with various keyboard layouts (34-key, 42-key, etc.)
- [ ] Test edge cases (empty layers, missing files)

## Documentation

- [ ] README with installation and usage
- [ ] Document all CLI options
- [ ] Add example configs
- [ ] Screenshots of output examples