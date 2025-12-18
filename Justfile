default:
    @just --list --unsorted

config := absolute_path('config')
build := absolute_path('.build')
out := absolute_path('firmware')
draw := absolute_path('draw')
artifacts := absolute_path('artifacts')

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

# build firmware for matching targets
build expr *west_args:
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
    git add {{ draw }}/*.{yaml,svg} 2>/dev/null || true

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

# clear build cache and artifacts
clean:
    rm -rf {{ build }} {{ out }}

# clear all automatically generated files
clean-all: clean
    rm -rf .west zmk

# clear nix cache
clean-nix:
    nix-collect-garbage --delete-old

# draw all diagrams
draw: draw-base draw-main draw-gaming draw-merged

# parse & plot keymap
draw-base:
    #!/usr/bin/env bash
    set -euo pipefail
    keymap -c "{{ draw }}/config.yaml" parse -z "{{ config }}/base.keymap" --virtual-layers Combos Gaming >"{{ draw }}/base.yaml"
    keymap -c "{{ draw }}/config.yaml" draw "{{ draw }}/base.yaml" -k "ferris/sweep" >"{{ draw }}/base.svg"

# parse & plot MAIN KEYMAP
draw-main:
    #!/usr/bin/env bash
    set -euo pipefail
    keymap -c "{{ draw }}/config.yaml" parse -z "{{ config }}/base.keymap" --virtual-layers Combos >"{{ draw }}/combos_main.yaml"
    yq -Yi '.combos = [.combos[] | select(.l | length > 0) | select(.l[] | test("colemak","qwerty","nav","num", "fun", "uti"))]' "{{ draw }}/combos_main.yaml"
    yq -Yi '.layers."MAIN_COMBOS" = [range(34) | ""] | .combos.[].l = ["MAIN_COMBOS"]' "{{ draw }}/combos_main.yaml"
    keymap -c "{{ draw }}/config.yaml" draw "{{ draw }}/combos_main.yaml" -k "ferris/sweep" -s l_colemak_dh l_nav l_num l_fun l_utility MAIN_COMBOS >"{{ draw }}/combos_main.svg"

# parse & plot GAMING KEYMAP
draw-gaming:
    #!/usr/bin/env bash
    set -euo pipefail
    keymap -c "{{ draw }}/config.yaml" parse -z "{{ config }}/base.keymap" --virtual-layers GAMING_COMBOS >"{{ draw }}/combos_gaming.yaml"
    yq -Yi '.combos = [.combos[] | select(.l | length > 0) | select(.l[] | test("l_gam"))]' "{{ draw }}/combos_gaming.yaml"
    yq -Yi '.layers."GAMING_COMBOS" = [range(34) | ""]| .combos.[].l = ["GAMING_COMBOS"]' "{{ draw }}/combos_gaming.yaml"
    keymap -c "{{ draw }}/config.yaml" draw "{{ draw }}/combos_gaming.yaml" -k "ferris/sweep" -s l_gam l_gam_num l_gam_r_alpha GAMING_COMBOS >"{{ draw }}/combos_gaming.svg"

# merge layers into single multi-position diagram with 7 legend positions
draw-merged *layers:
    #!/usr/bin/env bash
    set -euo pipefail
    # Call 1: Merge layers into YAML with 7 positions (t/s/h from center, tl/tr/bl/br from corners)
    python "{{ draw }}/merge_layers.py" \
        --input "{{ draw }}/base.yaml" \
        --center l_colemak_dh \
        --tl l_fun \
        --tr l_utility \
        --bl l_num \
        --br l_nav \
        --output "{{ draw }}/merged.yaml"
    # Strip tl/tr/bl/br keys (keymap-drawer only accepts t/s/h/left/right)
    yq '.layers.merged = [.layers.merged[] | if type == "object" then del(.tl, .tr, .bl, .br) else . end]' \
        "{{ draw }}/merged.yaml" > "{{ draw }}/merged_draw.yaml"
    # keymap-drawer renders t/s/h
    keymap -c "{{ draw }}/config.yaml" draw "{{ draw }}/merged_draw.yaml" -k "ferris/sweep" >"{{ draw }}/merged.svg"
    # Call 2: Post-process SVG to inject corner legends from full merged.yaml
    python "{{ draw }}/merge_layers.py" \
        --inject-corners "{{ draw }}/merged.svg" \
        --merged-yaml "{{ draw }}/merged.yaml" \
        --config "{{ draw }}/config.yaml" \
        --glyph-svg "{{ draw }}/base.svg" \
        --pad-x 0 --pad-y 0
    rm "{{ draw }}/merged_draw.yaml"
    echo "Created {{ draw }}/merged.svg with 7 legend positions"

# copy all built artifacts from /firmware and /draw to /out with timestamp in a time-stamped folder
copy-artifacts:
    #!/usr/bin/env bash
    date=$(date +%Y%m%d)
    dateTime=$(date +%Y%m%d_%H%M%S)
    mkdir -p "{{ artifacts }}/$date"
    cp {{ out }}/*.{uf2,bin} "{{ artifacts }}/$date" 2>/dev/null || true
    cp {{ draw }}/*.{yaml,svg} "{{ artifacts }}/$date" 2>/dev/null || true
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
