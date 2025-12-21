#!/usr/bin/env python3
"""
ZMK Keymap Formatter

Formats ZMK keymap files while preserving C preprocessor macros.
Handles:
- ZMK_LAYER: aligns key bindings into a grid
- ZMK_BEHAVIOR, ZMK_HOLD_TAP, ZMK_TAP_DANCE, ZMK_MACRO: consistent formatting
- Devicetree nodes: proper indentation
- Preprocessor directives: preserved as-is
"""

import re
import sys
import argparse
from pathlib import Path


def parse_zmk_layer(content: str) -> tuple[str, str, list[str]] | None:
    """Parse a ZMK_LAYER macro and extract name and bindings."""
    # Match ZMK_LAYER(name, bindings...)
    match = re.match(r'ZMK_LAYER\s*\(\s*(\w+)\s*,(.+)\)', content, re.DOTALL)
    if not match:
        return None

    name = match.group(1)
    bindings_str = match.group(2).strip()

    # Parse individual bindings (handle &xxx, &xxx PARAM, &xxx PARAM PARAM, etc.)
    bindings = []
    current = ""
    paren_depth = 0

    for char in bindings_str:
        if char == '(':
            paren_depth += 1
            current += char
        elif char == ')':
            paren_depth -= 1
            current += char
        elif char == '&' and paren_depth == 0:
            if current.strip():
                bindings.append(current.strip())
            current = "&"
        else:
            current += char

    if current.strip():
        bindings.append(current.strip())

    return name, bindings_str, bindings


def format_zmk_layer(name: str, bindings: list[str], cols: int = 10) -> str:
    """Format a ZMK_LAYER with aligned columns."""
    # Calculate column widths
    rows = [bindings[i:i+cols] for i in range(0, len(bindings), cols)]

    # Get max width for each column
    col_widths = []
    for col in range(cols):
        max_width = 0
        for row in rows:
            if col < len(row):
                max_width = max(max_width, len(row[col]))
        col_widths.append(max_width)

    # Format rows
    formatted_rows = []
    for i, row in enumerate(rows):
        formatted_keys = []
        for j, key in enumerate(row):
            if j < len(col_widths):
                # Don't pad the last key in a row
                if j == len(row) - 1:
                    formatted_keys.append(key)
                else:
                    formatted_keys.append(key.ljust(col_widths[j]))
        formatted_rows.append("    " + " ".join(formatted_keys))

    return f"ZMK_LAYER({name},\n" + "\n".join(formatted_rows) + "\n)"


def format_zmk_macro_block(macro_type: str, name: str, content: str) -> str:
    """Format ZMK_BEHAVIOR, ZMK_HOLD_TAP, etc."""
    # Clean up the content
    content = content.strip()

    # For ZMK_BEHAVIOR, first arg is the behavior type (mod_morph, sticky_key, etc.)
    # Keep it on the same line as the name
    behavior_type = None
    if macro_type == "ZMK_BEHAVIOR":
        # Extract first comma-separated argument as behavior type
        first_comma = -1
        depth = 0
        for i, char in enumerate(content):
            if char in '<(':
                depth += 1
            elif char in '>)':
                depth -= 1
            elif char == ',' and depth == 0:
                first_comma = i
                break
        if first_comma > 0:
            behavior_type = content[:first_comma].strip()
            content = content[first_comma+1:].strip()

    # Split into properties (handle ; as separator, respecting <> and () nesting)
    # Also handle // comments - they attach to the preceding property
    properties = []
    current = ""
    angle_depth = 0
    paren_depth = 0
    in_comment = False

    i = 0
    while i < len(content):
        char = content[i]

        # Check for // comment start
        if not in_comment and char == '/' and i + 1 < len(content) and content[i + 1] == '/':
            in_comment = True
            current += char
            i += 1
            continue

        # End comment on newline
        if in_comment and char == '\n':
            in_comment = False
            current += char
            i += 1
            continue

        if in_comment:
            current += char
            i += 1
            continue

        if char == '<':
            angle_depth += 1
        elif char == '>':
            angle_depth -= 1
        elif char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth -= 1
        elif char == ';' and angle_depth == 0 and paren_depth == 0:
            if current.strip():
                properties.append(current.strip() + ";")
            current = ""
            i += 1
            continue
        current += char
        i += 1

    if current.strip():
        # Last property might not have semicolon (could be trailing comment)
        prop = current.strip()
        # Don't add semicolon to pure comments
        if not prop.startswith('//') and not prop.endswith(';'):
            prop += ";"
        properties.append(prop)

    if not properties and not behavior_type:
        return f"{macro_type}({name}, {content})"

    # Normalize property indentation (strip leading whitespace from each)
    normalized_props = []
    for prop in properties:
        # Handle multi-line properties (with embedded newlines)
        lines = prop.split('\n')
        normalized_lines = [lines[0].strip()]  # First line
        for line in lines[1:]:
            normalized_lines.append(line.strip())
        normalized_props.append('\n    '.join(normalized_lines))

    # Format with proper indentation
    formatted_props = "\n".join(f"    {prop}" for prop in normalized_props)

    if behavior_type:
        return f"{macro_type}({name}, {behavior_type},\n{formatted_props}\n)"
    else:
        return f"{macro_type}({name},\n{formatted_props}\n)"


def format_devicetree_node(content: str) -> str:
    """Format a devicetree node reference like &sk { ... }.

    Preserves original indentation to avoid breaking inline comments.
    Only normalizes the opening and closing structure.
    """
    lines = content.split('\n')
    if not lines:
        return content

    formatted = []
    first_line = lines[0]

    # First line: node opener like "&sk {" - keep as is
    formatted.append(first_line.rstrip())

    # Middle lines: preserve their relative indentation
    for line in lines[1:-1] if len(lines) > 2 else []:
        formatted.append(line.rstrip())

    # Last line: closing brace if multiline
    if len(lines) > 1:
        formatted.append(lines[-1].rstrip())

    return '\n'.join(formatted)


def is_in_backslash_continuation(lines: list[str], index: int) -> bool:
    """Check if we're inside a backslash-continued macro definition."""
    # Look backwards for a line starting with #define that continues with backslash
    for j in range(index - 1, -1, -1):
        prev_line = lines[j]
        if prev_line.rstrip().endswith('\\'):
            # Check if this chain started with #define
            k = j
            while k > 0 and lines[k-1].rstrip().endswith('\\'):
                k -= 1
            if lines[k].strip().startswith('#define'):
                return True
        else:
            # No continuation, stop looking
            break
    return False


def format_keymap(content: str, cols: int = 10) -> str:
    """Format an entire keymap file."""
    result = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip backslash-continued macro definitions entirely
        if stripped.startswith('#define') and line.rstrip().endswith('\\'):
            # Collect entire macro definition
            while i < len(lines) and lines[i].rstrip().endswith('\\'):
                result.append(lines[i])
                i += 1
            # Add the final line (without backslash)
            if i < len(lines):
                result.append(lines[i])
                i += 1
            continue

        # Skip if we're somehow inside a continuation (shouldn't happen with above logic)
        if is_in_backslash_continuation(lines, i):
            result.append(line)
            i += 1
            continue

        # Handle ZMK_LAYER - collect until closing paren
        if stripped.startswith('ZMK_LAYER('):
            macro_content = line
            paren_depth = line.count('(') - line.count(')')

            while paren_depth > 0 and i + 1 < len(lines):
                i += 1
                macro_content += '\n' + lines[i]
                paren_depth += lines[i].count('(') - lines[i].count(')')

            parsed = parse_zmk_layer(macro_content)
            if parsed:
                name, _, bindings = parsed
                result.append(format_zmk_layer(name, bindings, cols))
            else:
                result.append(macro_content)
            i += 1
            continue

        # Handle ZMK_BEHAVIOR, ZMK_HOLD_TAP, ZMK_TAP_DANCE, ZMK_MACRO
        macro_match = re.match(r'(ZMK_BEHAVIOR|ZMK_HOLD_TAP|ZMK_TAP_DANCE|ZMK_MACRO)\s*\(\s*(\w+)\s*,', stripped)
        if macro_match:
            macro_type = macro_match.group(1)
            macro_name = macro_match.group(2)

            macro_content = line
            paren_depth = line.count('(') - line.count(')')

            while paren_depth > 0 and i + 1 < len(lines):
                i += 1
                macro_content += '\n' + lines[i]
                paren_depth += lines[i].count('(') - lines[i].count(')')

            # Extract content after name
            full_match = re.search(rf'{macro_type}\s*\(\s*{macro_name}\s*,(.+)\)', macro_content, re.DOTALL)
            if full_match:
                inner_content = full_match.group(1).strip()
                result.append(format_zmk_macro_block(macro_type, macro_name, inner_content))
            else:
                result.append(macro_content)
            i += 1
            continue

        # Handle devicetree node references like &sk { ... }
        if re.match(r'&\w+\s*\{', stripped):
            node_content = line
            brace_depth = line.count('{') - line.count('}')

            while brace_depth > 0 and i + 1 < len(lines):
                i += 1
                node_content += '\n' + lines[i]
                brace_depth += lines[i].count('{') - lines[i].count('}')

            result.append(format_devicetree_node(node_content))
            i += 1
            continue

        # Pass through everything else unchanged
        result.append(line)
        i += 1

    # Clean up multiple blank lines
    formatted = '\n'.join(result)
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)

    return formatted


def main():
    parser = argparse.ArgumentParser(description='Format ZMK keymap files')
    parser.add_argument('file', help='Keymap file to format')
    parser.add_argument('-c', '--cols', type=int, default=10,
                        help='Number of columns per row (default: 10 for split keyboards)')
    parser.add_argument('-i', '--in-place', action='store_true',
                        help='Edit file in place')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')

    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    content = path.read_text()
    formatted = format_keymap(content, args.cols)

    if args.in_place:
        path.write_text(formatted)
        print(f"Formatted {path}")
    elif args.output:
        Path(args.output).write_text(formatted)
        print(f"Wrote {args.output}")
    else:
        print(formatted)


if __name__ == '__main__':
    main()
