#!/usr/bin/env python3
"""Append combos_main_standalone.svg to the bottom of merged.svg"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def main():
    if len(sys.argv) != 3:
        print("Usage: append_combos.py <merged.svg> <combos.svg>")
        sys.exit(1)

    merged_path, combos_path = sys.argv[1], sys.argv[2]

    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

    merged = ET.parse(merged_path)
    combos = ET.parse(combos_path)
    mr, cr = merged.getroot(), combos.getroot()

    # Parse viewBox dimensions
    mv = [float(x) for x in mr.get('viewBox').split()]
    cv = [float(x) for x in cr.get('viewBox').split()]

    # Create group with combos content, translated below merged
    g = ET.SubElement(mr, 'g', transform=f'translate(0,{mv[3]})')
    for child in list(cr):
        if child.tag != '{http://www.w3.org/2000/svg}defs':
            g.append(child)

    # Merge defs
    mdefs = mr.find('{http://www.w3.org/2000/svg}defs')
    cdefs = cr.find('{http://www.w3.org/2000/svg}defs')
    if cdefs is not None and mdefs is not None:
        for child in cdefs:
            if child.get('id') and mr.find(f'.//*[@id="{child.get("id")}"]') is None:
                mdefs.append(child)

    # Update viewBox and dimensions
    mr.set('viewBox', f'{mv[0]} {mv[1]} {max(mv[2],cv[2])} {mv[3]+cv[3]}')
    mr.set('height', str(mv[3]+cv[3]))
    mr.set('width', str(max(mv[2],cv[2])))

    merged.write(merged_path, xml_declaration=False)

if __name__ == '__main__':
    main()
