import json
import os
import csv
from xml.dom import minidom
from collections import defaultdict, Counter
import unicodedata

# --- CONFIGURATION ---
svg_file = r"E:\Maps\empire_political.svg"
target_layer = "Settlement Labels"
output_geojson = "settlements.geojson"
geojson_dir = os.path.dirname(svg_file)

# --- LOAD EXISTING GEOJSON ---
if os.path.exists(output_geojson):
    with open(output_geojson, "r", encoding="utf-8") as f:
        geojson = json.load(f)
        existing_features = geojson.get("features", [])
else:
    geojson = {"type": "FeatureCollection", "features": []}
    existing_features = []

# --- BUILD LOOKUP FOR EXISTING FEATURES ---
existing_lookup = {
    (f["properties"]["name"], f["properties"]["province"]): f
    for f in existing_features
    if f["properties"].get("name") and f["properties"].get("province")
}

# --- LOAD SVG ---
doc = minidom.parse(svg_file)

def get_label(element):
    return element.getAttribute("inkscape:label") or element.getAttribute("sodipodi:label")

def set_label(element, new_label):
    if element.hasAttribute("inkscape:label"):
        element.setAttribute("inkscape:label", new_label)
    elif element.hasAttribute("sodipodi:label"):
        element.setAttribute("sodipodi:label", new_label)
    else:
        element.setAttribute("inkscape:label", new_label)

def extract_text_content(text_element):
    for node in text_element.childNodes:
        if node.nodeType == node.TEXT_NODE:
            return node.data.strip()
        if node.nodeType == node.ELEMENT_NODE and node.tagName == "tspan":
            return node.firstChild.data.strip() if node.firstChild else ""
    return ""

def extract_coordinates(text_element):
    x = text_element.getAttribute("x")
    y = text_element.getAttribute("y")
    if not x or not y:
        tspans = text_element.getElementsByTagName("tspan")
        if tspans:
            x = tspans[0].getAttribute("x")
            y = tspans[0].getAttribute("y")
    try:
        return [float(x) + 3.0 , float(y) + 3.9]
    except:
        return None

# --- LOAD GAZETTEERS ---
gazetteers = defaultdict(dict)
unmatched_gazetteer_entries = defaultdict(list)

for fname in os.listdir(geojson_dir):
    if fname.endswith("_Gazetteer.csv"):
        province = fname.split("_Gazetteer.csv")[0]
        print(f"📍 Found gazetteer for {province}.")
        path = os.path.join(geojson_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0].strip():
                    continue
                name = row[0].strip()
                population = int(row[1]) if len(row) > 1 and row[1].strip().isdigit() else None
                estate = row[2].strip() if len(row) > 2 and row[2].strip() else None
                notes = row[3].strip() if len(row) > 3 and row[3].strip() else None
                key = (name, province)
                if key in gazetteers:
                    print(f"⚠️ Duplicate name in Gazetteer: {name} in {province}")
                gazetteers[key] = {
                    "population": population,
                    "estate": estate,
                    "notes": notes
                }

# --- TRACK DUPLICATES ---
name_province_counter = Counter()
# --- PARSE SVG TEXTS ---
def collect_features(layer, current_path):
    new_features = 0
    updated_features = 0

    layer_label = get_label(layer)
    if layer_label:
        current_path = current_path + [layer_label]

    for node in layer.childNodes:
        if node.nodeType != node.ELEMENT_NODE:
            continue

        if node.tagName == "g":
            nf, uf = collect_features(node, current_path)
            new_features += nf
            updated_features += uf

        elif node.tagName == "text":
            name = extract_text_content(node)
            coords = extract_coordinates(node)
            province = current_path[-1] if current_path else None
            svg_id = node.getAttribute("id")

            if not name or not coords or not province:
                continue

            key = (name, province)
            name_province_counter[key] += 1

            # Sync label
            set_label(node, name)

            # Lookup or add new
            if key in existing_lookup:
                feature = existing_lookup[key]
                feature["geometry"]["coordinates"] = coords
                feature["properties"]["svg_id"] = svg_id
                updated_features += 1
            else:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": name,
                        "type": None,
                        "province": province,
                        "estate": None,
                        "population": None,
                        "notes": None,
                        "svg_id": svg_id
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": coords
                    }
                }
                existing_features.append(feature)
                existing_lookup[key] = feature
                new_features += 1

            # Gazetteer matching
            if key in gazetteers:
                g_entry = gazetteers.pop(key)
                feature["properties"].update(g_entry)

    return new_features, updated_features

# --- FIND TARGET LAYER ---
for g in doc.getElementsByTagName("g"):
    if get_label(g) == target_layer:
        print(f"📍 Found layer: {target_layer}")
        new_count, updated_count = collect_features(g, [])
        break
else:
    print("❌ Target layer not found.")
    new_count = updated_count = 0

doc.unlink()

# --- SAVE GEOJSON ---
geojson["features"] = list(existing_features)
with open(output_geojson, "w", encoding="utf-8") as f:
    json.dump(geojson, f, indent=2)

# --- REPORTING ---
print(f"\n✅ GeoJSON updated.")
print(f"🆕 New features added: {new_count}")
print(f"🔁 Features updated: {updated_count}")

# --- REPORT UNMATCHED GAZETTEER ENTRIES ---
if gazetteers:
    print("\n⚠️ Unmatched entries in Gazetteers:")
    for (name, province) in sorted(gazetteers.keys()):
        print(f"  - {name} ({province})")

# --- REPORT DUPLICATE NAMES IN PROVINCE ---
print("\n🔎 Duplicate settlement names within the same province:")
for (name, province), count in name_province_counter.items():
    if count > 1:
        print(f"  - {name} ({province}) ×{count}")
