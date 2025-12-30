#!/usr/bin/env bash
# Check that SYS layer has the highest priority (highest layer number)
# SYS must overlay all other layers

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${1:-$(dirname "$SCRIPT_DIR")/config}"

# Known layer names to check
LAYER_NAMES="CMK_DH QWERTY NUM NAV FUN GAM GAM_NUM GAM_RA SYS"

# Extract layer number for a given name
get_layer_num() {
    grep -rh --include="*.keymap" "#define $1 " "$CONFIG_DIR" 2>/dev/null |
        tr -d '\r' |
        head -1 |
        sed -E 's/.*#define [A-Z_]+ ([0-9]+).*/\1/'
}

# Build layer list
layers=""
for name in $LAYER_NAMES; do
    num=$(get_layer_num "$name")
    if [[ -n "$num" ]]; then
        layers+="$name $num"$'\n'
    fi
done

if [[ -z "$layers" ]]; then
    echo "WARNING: No layer definitions found"
    exit 0
fi

# Get SYS layer number
SYS=$(echo "$layers" | grep "^SYS " | awk '{print $2}')

if [[ -z "$SYS" ]]; then
    echo "WARNING: SYS layer not found"
    exit 0
fi

errors=0

# Check SYS against all other layers
while IFS=' ' read -r layer_name layer_num; do
    [[ "$layer_name" == "SYS" ]] && continue

    if [[ "$SYS" -le "$layer_num" ]]; then
        echo "ERROR: SYS ($SYS) must be higher than $layer_name ($layer_num)"
        ((errors++))
    fi
done <<< "$layers"

if [[ $errors -gt 0 ]]; then
    echo ""
    echo "SYS needs the highest layer number to overlay all other layers."
    echo "Fix: Move SYS definition to the end with the highest number."
    exit 1
fi

echo "Layer priority OK: SYS ($SYS) is highest"
