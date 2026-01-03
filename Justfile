default:
    @just --list --unsorted

config := absolute_path('config')
build := absolute_path('.build')
out := absolute_path('firmware')
draw := absolute_path('draw')
draw_in := draw / "inputs"
draw_kd := draw / "outputs/keymap_drawer"
draw_merged := draw / "outputs/merged"
artifacts := absolute_path('artifacts')

# check for duplicate combo names and layer priority
check:
    @scripts/checks/check_combos.sh
    @scripts/checks/check_layers.sh

# parse build.yaml and filter targets by expression
_parse_targets $expr:
    #!/usr/bin/env bash
    attrs="[.board, .shield, .snippet, .\"artifact-name\"]"
    filter="(($attrs | map(. // [.]) | combinations), ((.include // {})[] | $attrs)) | join(\",\")"
    echo "$(yq -r "$filter" build.yaml | grep -v "^," | grep -i "${expr/#all/.*}")"

# build firmware for single board & shield combination
_build_single $board $shield $snippet $artifact *west_args:
    #!/usr/bin/env bash
    set -euo pipefail

    # get date for unique artifact names
    artifact="${artifact:-${shield:+${shield// /+}-}${board}}"
    build_dir="{{ build / '$artifact' }}"

    echo "Building firmware for $artifact..."
    west build -s zmk/app -d "$build_dir" -b $board {{ west_args }} ${snippet:+-S "$snippet"} -- \
        -DZMK_CONFIG="{{ config }}" ${shield:+-DSHIELD="$shield"}

    if [[ -f "$build_dir/zephyr/zmk.uf2" ]]; then
        mkdir -p "{{ out }}" && cp "$build_dir/zephyr/zmk.uf2" "{{ out }}/$artifact.uf2"
    else
        mkdir -p "{{ out }}" && cp "$build_dir/zephyr/zmk.bin" "{{ out }}/$artifact.bin"
    fi

# build firmware for matching targets (runs check first)
build expr *west_args: check
    #!/usr/bin/env bash
    set -euo pipefail
    targets=$(just _parse_targets {{ expr }})
    [[ -z $targets ]] && echo "No matching targets found. Aborting..." >&2 && exit 1
    echo "$targets" | while IFS=, read -r board shield snippet artifact; do
        just _build_single "$board" "$shield" "$snippet" "$artifact" {{ west_args }}
    done

# build firmware and autocommit changes
release expr *west_args:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "Building firmware for {{ expr }}..."
    just build {{ expr }} {{ west_args }}

    echo "Adding firmware files to git..."
    git add {{ out }}/*.{uf2,bin} 2>/dev/null || true

    echo "Drawing combo diagrams..."
    just draw

    echo "Copying artifacts to timestamped folder..."
    just copy-artifacts

    echo "Adding diagram files to git..."
    git add {{ draw_kd }}/*.{yaml,svg} {{ draw_merged }}/*.{yaml,svg} 2>/dev/null || true

autocommit $model:
    #!/usr/bin/env bash
    set -euo pipefail
    # Check if there are changes to commit
    if git diff --cached --quiet; then
        echo "No new firmware files to commit."
    else
        date=$(date +%Y%m%d_%H%M)
        git commit -m "feat: update firmware build for $model - $date"
        echo "Committed firmware build for $model"
    fi

# format ZMK keymap files
fmt *files:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -z "{{ files }}" ]]; then
        python3 scripts/zmk_format.py -i "{{ config }}/base.keymap"
    else
        for f in {{ files }}; do
            python3 scripts/zmk_format.py -i "$f"
        done
    fi

# clear build cache and artifacts
clean:
    rm -rf {{ build }} {{ out }}

# clear all automatically generated files
clean-all: clean
    rm -rf .west zmk

# clear nix cache
clean-nix:
    nix-collect-garbage --delete-old

# you burned it all with a formatter? lucky you
clean-init: clean-all
    rm -rf modules zephyr
    just init

# draw all diagrams
draw: draw-base draw-merged draw-merged-gaming
    code {{ draw_merged }}/merged.svg || true

# parse & plot keymap
draw-base:
    #!/usr/bin/env bash
    set -euo pipefail
    keymap -c "{{ draw_in }}/config.yaml" parse -z "{{ config }}/base.keymap" --virtual-layers Combos Gaming >"{{ draw_kd }}/base.yaml"
    keymap -c "{{ draw_in }}/config.yaml" draw "{{ draw_kd }}/base.yaml" -k "ferris/sweep" >"{{ draw_kd }}/base.svg"

# --- Theme-based merged diagram generation ---
# Themes defined in draw/inputs/themes.yaml with colors: tl tr bl br text bg combo_bg

# Generate merged diagram for a specific theme (internal helper)
_draw-merged-theme $theme_name:
    #!/usr/bin/env bash
    set -euo pipefail
    theme_yaml="{{ draw_in }}/themes.yaml"
    config_yaml="{{ draw_in }}/config.yaml"

    # Extract theme settings from themes.yaml
    dark=$(yq -r ".themes.${theme_name}.dark_mode // false" "$theme_yaml")

    output_svg="{{ draw_merged }}/merged_${theme_name}.svg"

    # Create temporary config with theme's dark_mode setting
    temp_config="{{ draw }}/config_${theme_name}.yaml"
    yq ".draw_config.dark_mode = $dark" "$config_yaml" > "$temp_config"

    # Stack layers and draw
    keymap -c "$temp_config" stack-layers \
        "{{ draw_kd }}/base.yaml" \
        --center cmk_dh --tl fun --tr sys --bl num --br nav \
        --include-combos cmk_dh nav num fun sys \
        --separate-combo-layer \
        -o "{{ draw_merged }}/merged.yaml"

    keymap -c "$temp_config" draw "{{ draw_merged }}/merged.yaml" \
        -k "ferris/sweep" -o "$output_svg"

    rm "$temp_config"
    echo "Created $output_svg"

# Generate all themed merged SVGs (merged_<theme>.svg for each theme in themes.yaml)
draw-merged-all: draw-base
    #!/usr/bin/env bash
    set -euo pipefail
    theme_yaml="{{ draw_in }}/themes.yaml"
    themes=$(yq -r '.themes | keys | .[]' "$theme_yaml")

    for theme in $themes; do
        just _draw-merged-theme "$theme"
    done

    echo "Generated themed SVGs: $(echo $themes | tr '\n' ' ')"

# Generate merged diagram using default theme from themes.yaml (outputs merged.svg)
draw-merged: draw-base
    #!/usr/bin/env bash
    set -euo pipefail
    theme_yaml="{{ draw_in }}/themes.yaml"
    default_theme=$(yq -r '.default // "light"' "$theme_yaml")

    just _draw-merged-theme "$default_theme"

    # Copy to merged.svg for backwards compatibility
    cp "{{ draw_merged }}/merged_${default_theme}.svg" "{{ draw_merged }}/merged.svg"

    echo "Created {{ draw_merged }}/merged.svg (theme: $default_theme)"

# Generate merged gaming diagram
draw-merged-gaming: draw-base
    #!/usr/bin/env bash
    set -euo pipefail
    config_yaml="{{ draw_in }}/config.yaml"

    # Stack gaming layers
    keymap -c "$config_yaml" stack-layers \
        "{{ draw_kd }}/base.yaml" \
        --center gam --bl gam_num --br gam_ra \
        --include-combos gam gam_num gam_ra \
        --separate-combo-layer \
        -o "{{ draw_merged }}/merged_gaming.yaml"

    keymap -c "$config_yaml" draw "{{ draw_merged }}/merged_gaming.yaml" \
        -k "ferris/sweep" -o "{{ draw_merged }}/merged_gaming.svg"

    echo "Created {{ draw_merged }}/merged_gaming.svg"

# copy all built artifacts from /firmware and /draw to /out with timestamp in a time-stamped folder
copy-artifacts:
    #!/usr/bin/env bash
    date=$(date +%Y%m%d)
    dateTime=$(date +%Y%m%d_%H%M%S)
    mkdir -p "{{ artifacts }}/$date"
    cp {{ out }}/*.{uf2,bin} "{{ artifacts }}/$date" 2>/dev/null || true
    cp {{ draw_kd }}/*.{yaml,svg} "{{ artifacts }}/$date" 2>/dev/null || true
    cp {{ draw_merged }}/*.{yaml,svg} "{{ artifacts }}/$date" 2>/dev/null || true
    echo "Copied artifacts to {{ artifacts }}/$date"

# initialize west
init:
    west init -l config
    west update --fetch-opt=--filter=blob:none
    west zephyr-export

# list build targets
list:
    @just _parse_targets all | sed 's/,*$//' | sort | column

# update west
update:
    west update --fetch-opt=--filter=blob:none

# upgrade zephyr-sdk and python dependencies
upgrade-sdk:
    nix flake update --flake .

[no-cd]
test $testpath *FLAGS:
    #!/usr/bin/env bash
    set -euo pipefail
    testcase=$(basename "$testpath")
    build_dir="{{ build / "tests" / '$testcase' }}"
    config_dir="{{ '$(pwd)' / '$testpath' }}"
    cd {{ justfile_directory() }}

    if [[ "{{ FLAGS }}" != *"--no-build"* ]]; then
        echo "Running $testcase..."
        rm -rf "$build_dir"
        west build -s zmk/app -d "$build_dir" -b native_posix_64 -- \
            -DCONFIG_ASSERT=y -DZMK_CONFIG="$config_dir"
    fi

    ${build_dir}/zephyr/zmk.exe | sed -e "s/.*> //" |
        tee ${build_dir}/keycode_events.full.log |
        sed -n -f ${config_dir}/events.patterns > ${build_dir}/keycode_events.log
    if [[ "{{ FLAGS }}" == *"--verbose"* ]]; then
        cat ${build_dir}/keycode_events.log
    fi

    if [[ "{{ FLAGS }}" == *"--auto-accept"* ]]; then
        cp ${build_dir}/keycode_events.log ${config_dir}/keycode_events.snapshot
    fi
    diff -auZ ${config_dir}/keycode_events.snapshot ${build_dir}/keycode_events.log
