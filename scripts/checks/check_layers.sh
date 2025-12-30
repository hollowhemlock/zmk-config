#!/usr/bin/env bash
# Check that ZMK layer definitions match their actual order
# and that sys is the last layer (highest priority)

set -euo pipefail

# Layer that must be last (highest priority, overlays all others)
OVERLAY_LAYER="sys"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEYMAP="${1:-$(dirname "$(dirname "$SCRIPT_DIR")")/config/base.keymap}"

if [[ ! -f "$KEYMAP" ]]; then
    echo "ERROR: Keymap not found: $KEYMAP"
    exit 1
fi

# Extract ZMK_LAYER calls in order (lowercase names, skip macro definitions)
mapfile -t layers < <(grep -E "^ZMK_LAYER\([a-z_]+," "$KEYMAP" | tr -d '\r' | sed 's/ZMK_LAYER(//;s/,//')

if [[ ${#layers[@]} -eq 0 ]]; then
    echo "WARNING: No ZMK_LAYER calls found"
    exit 0
fi

# Extract #define LAYERNAME N (uppercase names -> index)
declare -A defines
while IFS= read -r line; do
    line=$(echo "$line" | tr -d '\r')
    name=$(echo "$line" | sed -E 's/#define ([A-Z_]+) .*/\1/')
    num=$(echo "$line" | sed -E 's/#define [A-Z_]+ ([0-9]+).*/\1/')
    defines["$name"]="$num"
done < <(grep -E "#define [A-Z_]+ [0-9]+" "$KEYMAP" | grep -v "COMBO\|KEYS\|THUMBS\|QUICK_TAP\|SMART_NUM")

errors=0

echo "Layer order:"
for i in "${!layers[@]}"; do
    layer="${layers[$i]}"
    upper=$(echo "$layer" | tr '[:lower:]' '[:upper:]')
    defined="${defines[$upper]:-}"

    if [[ -z "$defined" ]]; then
        echo "  $i: $layer (no #define found)"
    elif [[ "$defined" -eq "$i" ]]; then
        echo "  $i: $layer (defined: $defined) ✓"
    else
        echo "  $i: $layer (defined: $defined) ✗ MISMATCH"
        ((errors++))
    fi
done

# Check overlay layer is last
last_layer="${layers[-1]}"
if [[ "$last_layer" != "$OVERLAY_LAYER" ]]; then
    echo ""
    echo "ERROR: $OVERLAY_LAYER must be the last layer for highest priority"
    echo "       Found '$last_layer' as last layer instead"
    ((errors++))
fi

if [[ $errors -gt 0 ]]; then
    echo ""
    echo "Fix: Ensure #define values match ZMK_LAYER order, and $OVERLAY_LAYER is last."
    exit 1
fi

echo ""
echo "Layer priority OK: $OVERLAY_LAYER is last"
