#!/usr/bin/env bash
# Check for duplicate ZMK combo names across all .dtsi files
# Exit with error if duplicates found

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${1:-$(dirname "$SCRIPT_DIR")/config}"

# Find all combo definitions and extract names
duplicates=$(
    grep -rh --include="*.dtsi" --include="*.keymap" "ZMK_COMBO(" "$CONFIG_DIR" 2>/dev/null |
    grep -v "^[[:space:]]*//" |  # skip commented lines
    sed -E 's/.*ZMK_COMBO\(([^,]+),.*/\1/' |
    sort |
    uniq -d
)

if [[ -n "$duplicates" ]]; then
    echo "ERROR: Duplicate combo names found:"
    echo "$duplicates" | while read -r name; do
        echo "  - $name"
        # Show where each duplicate is defined
        grep -rn --include="*.dtsi" --include="*.keymap" -F "ZMK_COMBO($name," "$CONFIG_DIR" 2>/dev/null |
            sed 's/^/      /'
    done
    echo ""
    echo "Each combo must have a unique name. Later definitions silently override earlier ones."
    exit 1
fi

echo "No duplicate combo names found."
