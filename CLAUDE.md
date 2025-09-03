# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

### Building Firmware
```bash
# ZMK builds are handled via GitHub Actions automatically on push/PR
# Check build.yaml for board/shield configurations
# Manual builds can be triggered via workflow_dispatch in GitHub Actions
```

### Keymap Visualization
```bash
# Generate keymap SVG diagrams using keymap-drawer
cd keymap-drawer
# Configuration files: my_config.yaml, sweep_keymap.yaml
# Output: sweep_keymap.ortho.svg
```

## Project Structure

This is a ZMK (Zephyr Mechanical Keyboard) configuration repository for a Cradio keyboard with advanced features including:

### Core Configuration Files
- **`build.yaml`**: GitHub Actions matrix defining board/shield combinations for firmware builds
- **`config/cradio.keymap`**: Main keymap definition with multiple layers and advanced behaviors
- **`config/cradio.conf`**: ZMK configuration settings (combo limits, Bluetooth settings)
- **`config/west_og_for_urob_merge.yml`**: West manifest file importing urob's ZMK modules

### Architecture Overview

This configuration uses a hybrid approach combining:
1. **Standard ZMK syntax** for basic keymap structure
2. **urob/zmk-config abstractions** for advanced features via helper modules

### Key Features Implemented

1. **Multi-layer Layout System**:
   - `COLEMAK_DH` (0): Primary Colemak-DH layout
   - `QWERTY` (1): Alternative QWERTY layout  
   - `GAMING_LAYER` (2): Optimized for gaming with left-hand clusters
   - `NUMBER_LAYER` (3): Numeric input with num-word functionality
   - `NAV_LAYER` (4): Navigation and editing commands
   - `FUN_LAYER` (5): Function keys and media controls
   - `UTILITY` (6): System settings (layer switching, Bluetooth, bootloader)
   - `GAMING_NUMBER_LAYER` (7): Gaming-specific numbers
   - `GAMING_RIGHT_ALPHA_LAYER` (8): Right-hand alpha for gaming
   - `UC` (9): Unicode characters (Greek letters, German characters)

2. **Advanced Behaviors** (using urob's "timeless" homerow mods approach):
   - **Positional Homerow Mods**: Uses `balanced` flavor with `require-prior-idle-ms` to prevent accidental mod activation during rolls
   - **Smart Shift**: Sticky shift with caps-word on double-tap (mod-morph behavior)
   - **Num-word**: Automatic number layer deactivation after non-numeric input
   - **Mod-morphs**: Context-sensitive punctuation (comma/semicolon, dot/colon)
   - **Hold-tap optimizations**: `hold-trigger-on-release` for more reliable homerow mods

3. **Combo System**: Extensive combo definitions in `config/includes/combos.dtsi`
   - Horizontal combos for common actions (Enter, Tab, Escape)
   - Vertical combos for symbols and punctuation
   - Gaming-specific combos for numbers and common key combinations
   - Two-handed combos for layer access

4. **Module Dependencies**:
   - `zmk-helpers`: urob's helper macros for simplified ZMK configuration
     - `ZMK_BEHAVIOR`: Generic behavior creation (used for comma_morph, dot_morph, smart_shft)
     - `ZMK_HOLD_TAP`: Hold-tap behaviors (smart_num)  
     - `ZMK_TAP_DANCE`: Tap-dance behaviors (num_dance)
     - `ZMK_COMBO`: Simplified combo definitions in combos.dtsi
   - `zmk-auto-layer`: Auto-layer functionality for num-word
   - Unicode character definitions for German and Greek letters

### File Organization

- **`config/includes/`**: Modular behavior and combo definitions
  - `behaviors_homerow_mods.dtsi`: Homerow mod behavior definitions
  - `combos.dtsi`: Complete combo key definitions with position mappings

- **`keymap-drawer/`**: Visualization tools and configurations
  - Contains SVG generation configs for keymap documentation

### Development Notes

- Configuration uses urob's zmk-config modules imported via West manifest
- Combo system supports up to 8 combos per key with 3-key combinations max
- Gaming layer designed for left-hand operation with number combos
- Unicode layer currently configured for Linux/macOS (Windows requires different definitions)
- Bluetooth power optimized with TX_PWR_PLUS_8 setting

### Build Configuration

The `build.yaml` file defines three build targets:
- `nice_nano_v2` + `cradio_left`
- `nice_nano_v2` + `cradio_right` 
- `nice_nano_v2` + `settings_reset`

Builds are triggered automatically via GitHub Actions on push, pull request, or manual dispatch.