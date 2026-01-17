import json
import os
import csv
from xml.dom import minidom
from collections import defaultdict, Counter

# --- INPUT FILE ---
svg_path = r"E:\Maps\bloopp.svg"
output_path = svg_path  # Overwrite original file or change if desired
output_geojson = "settlements.geojson"
geojson_dir = os.path.dirname(svg_path)

# --- TARGET LAYER ---
target_layer = "Settlement Labels for Display"

# --- Load SVG ---
doc = minidom.parse(svg_path)

def get_label(element):
    return element.getAttribute("inkscape:label") or element.getAttribute("sodipodi:label")

def set_label(element, name):
    element.setAttribute("inkscape:label", name)

def extract_text_content(text_element):
    for node in text_element.childNodes:
        if node.nodeType == node.TEXT_NODE:
            return node.data.strip()
        if node.nodeType == node.ELEMENT_NODE and node.tagName == "tspan":
            return node.firstChild.data.strip() if node.firstChild else ""
    return ""

def process_text_labels(layer):
    changed = 0
    for node in layer.childNodes:
        if node.nodeType != node.ELEMENT_NODE:
            continue

        if node.tagName == "g":
            changed += process_text_labels(node)

        elif node.tagName == "text":
            text_val = extract_text_content(node)
            if text_val:
                set_label(node, text_val)
                changed += 1

    return changed

# --- Find Layer ---
for g in doc.getElementsByTagName("g"):
    if get_label(g) == target_layer:
        count = process_text_labels(g)
        print(f"✅ Updated {count} text object labels in '{target_layer}' layer.")
        break
else:
    print("⚠️ Target layer not found.")

# --- Save Output ---
with open(output_path, "w", encoding="utf-8") as f:
    doc.writexml(f)

doc.unlink()
