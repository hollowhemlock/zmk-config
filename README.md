## ZMK Keyboard Config

![keymap](draw/outputs/merged/merged.svg)

### Setup

```bash
pipx install keymap-drawer  # Install keymap visualization tool
just setup-hooks            # Enable automatic keymap formatting on commit
```

### Usage

```bash
just build cradio    # Build firmware
just check           # Check for duplicate combos + layer priority
just fmt             # Format keymap files
just draw            # Generate keymap diagrams
just release cradio  # Build + draw + copy artifacts
just list            # List all build targets
```

### References

- [urob/zmk-config](https://github.com/urob/zmk-config)
- [urob/zmk-helpers](https://github.com/urob/zmk-helpers)
- [caksoylar/keymap-drawer](https://github.com/caksoylar/keymap-drawer)
