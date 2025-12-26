#!/usr/bin/env python3
"""
Backwards-compatible wrapper for keymap_merge.svg.combiner.

Usage (legacy):
    python append_combos.py <merged.svg> <combos.svg>

Usage (new):
    python -m keymap_merge combine <merged.svg> <combos.svg>
"""

import sys
from pathlib import Path

# Add scripts directory to path for package import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from keymap_merge.svg.combiner import main

if __name__ == "__main__":
    main()
