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

echo "Checking layer definitions..."
echo ""
printf "%-6s %-12s %-14s %-14s %s\n" "index" "name" "#define_name" "#define_value" "status"
printf "%.0s─" {1..60}
echo ""

for i in "${!layers[@]}"; do
    layer="${layers[$i]}"
    upper=$(echo "$layer" | tr '[:lower:]' '[:upper:]')
    defined="${defines[$upper]:-}"

    if [[ -z "$defined" ]]; then
        printf "%-6s %-12s %-14s %-14s %s\n" "$i" "$layer" "$upper" "-" "✗ no #define $upper found"
        ((errors++))
    elif [[ "$defined" -eq "$i" ]]; then
        printf "%-6s %-12s %-14s %-14s %s\n" "$i" "$layer" "$upper" "$defined" "✓"
    else
        printf "%-6s %-12s %-14s %-14s %s\n" "$i" "$layer" "$upper" "$defined" "✗ expected $i"
        ((errors++))
    fi
done

echo ""

# Check overlay layer is last
last_layer="${layers[-1]}"
if [[ "$last_layer" != "$OVERLAY_LAYER" ]]; then
    echo "✗ $OVERLAY_LAYER must be the last layer (found '$last_layer')"
    ((errors++))
else
    echo "✓ $OVERLAY_LAYER is last (highest priority)"
fi

if [[ $errors -gt 0 ]]; then
    echo ""
    echo "Fix: Ensure #define names match UPPERCASE of ZMK_LAYER names, values match order."
    exit 1
fi

echo "✓ All ${#layers[@]} layers validated"
