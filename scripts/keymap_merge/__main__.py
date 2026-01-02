"""CLI entry point for keymap_merge package.

Usage:
    python -m keymap_merge merge -i base.yaml --center cmk_dh -o merged.yaml
    python -m keymap_merge inject merged.svg --merged-yaml merged.yaml
    python -m keymap_merge combine merged.svg combos.svg
"""

from .cli import main

if __name__ == "__main__":
    main()
