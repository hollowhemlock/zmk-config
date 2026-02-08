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
check: fmt
    @scripts/checks/check_combos.sh
    @scripts/checks/check_layers.sh

# require command(s) to be available
_require_cmds *cmds:
    #!/usr/bin/env bash
    set -euo pipefail
    for c in {{ cmds }}; do
        command -v "$c" >/dev/null 2>&1 || { echo "Missing required command: $c" >&2; exit 1; }
    done

_require_build_deps:
    @just _require_cmds west yq

_require_draw_deps:
    @just _require_cmds keymap yq

_require_fmt_deps:
    @just _require_cmds python3

_require_test_deps:
    @just _require_cmds west

_require_nix_deps:
    @just _require_cmds nix nix-collect-garbage

_require_version $label $cmd $min $version_cmd:
    #!/usr/bin/env bash
    set -euo pipefail
    out=$({{ version_cmd }} 2>/dev/null || true)
    ver=$(echo "$out" | grep -Eo '[0-9]+(\.[0-9]+)+' | head -n1 || true)
    if [[ -z "$ver" ]]; then
        echo "Could not determine $label version from: $out" >&2
        exit 1
    fi
    if [[ "$(printf '%s\n' "$min" "$ver" | sort -V | head -n1)" != "$min" ]]; then
        echo "$label $ver is below required $min" >&2
        exit 1
    fi

_confirm_or_force $label:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${FORCE:-}" || -n "${CI:-}" || -n "${NO_PROMPT:-}" ]]; then
        exit 0
    fi
    if [[ -t 0 ]]; then
        read -r -p "Proceed with $label? (y/N) " ans
        [[ "$ans" == "y" || "$ans" == "Y" ]] || { echo "Aborted." >&2; exit 1; }
    else
        echo "Set FORCE=1 to run $label in non-interactive mode." >&2
        exit 1
    fi

# validate toolchain and inputs before building
preflight:
    @just _require_build_deps
    @just _require_draw_deps
    @just _require_fmt_deps
    @just _require_test_deps
    @just _require_version "west" west "1.5.0" "west --version"
    @just _require_version "yq (python)" yq "3.4.3" "yq --version"
    @just _require_version "keymap" keymap "0.22.1" "keymap --version"
    @just _require_version "python3" python3 "3.13.9" "python3 -c 'import sys; print(\"{}.{}.{}\".format(*sys.version_info[:3]))'"
    @test -f build.yaml
    @test -f "{{ config }}/base.keymap"
    @just _parse_targets all >/dev/null
    @echo "Preflight OK"

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
build expr *west_args: preflight check _require_build_deps
    #!/usr/bin/env bash
    set -euo pipefail
    targets=$(just _parse_targets {{ expr }})
    [[ -z $targets ]] && echo "No matching targets found. Aborting..." >&2 && exit 1
    while IFS=, read -r board shield snippet artifact; do
        just _build_single "$board" "$shield" "$snippet" "$artifact" {{ west_args }}
    done <<< "$targets"

# build firmware and autocommit changes (internal helper)
_release expr *west_args: preflight
    #!/usr/bin/env bash
    set -euo pipefail

    echo "Building firmware for {{ expr }}..."
    just build {{ expr }} {{ west_args }}

    echo "Skipping firmware git add (artifacts are produced by CI)."

    echo "Drawing combo diagrams..."
    just draw

    echo "Copying artifacts to timestamped folder..."
    just copy-artifacts

    echo "Adding diagram files to git..."
    diagram_files=( {{ draw_kd }}/*.{yaml,svg} {{ draw_merged }}/*.{yaml,svg} )
    if ((${#diagram_files[@]})); then
        git add "${diagram_files[@]}"
    else
        echo "No diagram artifacts found. Aborting..." >&2
        exit 1
    fi

# clean outputs then run release
release-clean expr *west_args: preflight
    #!/usr/bin/env bash
    set -euo pipefail
    just _confirm_or_force "release-clean (removes build and firmware outputs)"
    rm -rf {{ build }} {{ out }}
    just _release {{ expr }} {{ west_args }}

# release defaults to clean + release
release expr *west_args: preflight
    @just release-clean {{ expr }} {{ west_args }}

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
fmt *files: _require_fmt_deps
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
    @just _confirm_or_force "clean"
    rm -rf {{ build }} {{ out }}

# clear all automatically generated files
clean-all: clean
    @just _confirm_or_force "clean-all (removes .west and zmk)"
    rm -rf .west zmk

# clear nix cache
clean-nix: _require_nix_deps
    nix-collect-garbage --delete-old

# you burned it all with a formatter? lucky you
clean-init: clean-all
    @just _confirm_or_force "clean-init (removes modules and zephyr)"
    rm -rf modules zephyr
    just init

# draw all diagrams
draw: draw-base draw-merged draw-merged-gaming
    code {{ draw_merged }}/merged.svg || true

# parse & plot keymap
draw-base: _require_draw_deps
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
    shopt -s nullglob
    fw_files=( {{ out }}/*.{uf2,bin} )
    kd_files=( {{ draw_kd }}/*.{yaml,svg} )
    merged_files=( {{ draw_merged }}/*.{yaml,svg} )
    ((${#fw_files[@]})) && cp "${fw_files[@]}" "{{ artifacts }}/$date"
    ((${#kd_files[@]})) && cp "${kd_files[@]}" "{{ artifacts }}/$date"
    ((${#merged_files[@]})) && cp "${merged_files[@]}" "{{ artifacts }}/$date"
    if ! ((${#fw_files[@]} + ${#kd_files[@]} + ${#merged_files[@]})); then
        echo "No artifacts to copy." >&2
        exit 1
    fi
    echo "Copied artifacts to {{ artifacts }}/$date"

# initialize west
init: _require_build_deps
    #!/usr/bin/env bash
    set -euo pipefail
    # Disable fileMode on Windows to avoid permission conflicts with WSL
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OS" == "Windows_NT" ]]; then
        git config core.fileMode false
    fi
    west init -l config
    west update --fetch-opt=--filter=blob:none
    west zephyr-export

# list build targets
list:
    @just _parse_targets all | sed 's/,*$//' | sort | column

# update west
update: _require_build_deps
    west update --fetch-opt=--filter=blob:none

# configure git to use tracked hooks
setup-hooks:
    git config core.hooksPath .githooks
    @echo "Git hooks configured to use .githooks/"

# upgrade zephyr-sdk and python dependencies
upgrade-sdk: _require_nix_deps
    nix flake update --flake .

[no-cd]
test $testpath *FLAGS: _require_test_deps
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
