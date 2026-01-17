import json
import os
import xml.etree.ElementTree as ET

# --- CONFIGURATION ---
SVG_FILE = r"E:\Maps\the_old_world_SETTLEMENTS_POI_ROADS.svg"
GEOJSON_FILE = "settlements.geojson"

SETTLEMENT_LAYER_NAME = "DISPLAY Settlement Icons"
DISPLAY_LABEL_LAYER_NAME = "DISPLAY Settlement Labels"

# Population thresholds and styles
POPULATION_STYLES = [
    {"max": 300, "diameter": 0.2, "stroke": 0.05, "font_size": 2 / 3.779535, "font_style": "italic", "fill": "black"},
    {"max": 900, "diameter": 0.3, "stroke": 0.05, "font_size": 2.5 / 3.779535, "font_style": "normal"},
    {"max": 5000, "diameter": 0.5, "stroke": 0.05, "font_size": 3 / 3.779535, "font_style": "normal"},
    {"max": 14000, "diameter": 0.75, "stroke": 0.075, "font_size": 3.5 / 3.779535, "font_style": "bold"},
    {"max": float("inf"), "diameter": 1.0, "stroke": 0.10, "font_size": 4 / 3.779535, "font_style": "bold"},
]
NULL_POP_STYLE = {"diameter": 0.25, "stroke": 0.05, "font_size": 2, "font_style": "italic", "fill": "black"}

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
ET.register_namespace('', SVG_NS)
ET.register_namespace('inkscape', INKSCAPE_NS)

# --- FUNCTIONS ---
def get_style_for_population(pop):
    if pop is None:
        return NULL_POP_STYLE
    for style in POPULATION_STYLES:
        if pop <= style["max"]:
            return style
    return POPULATION_STYLES[-1]

def create_layer(label):
    layer = ET.Element(f'{{{SVG_NS}}}g')
    layer.set(f'{{{INKSCAPE_NS}}}label', label)
    layer.set(f'{{{INKSCAPE_NS}}}groupmode', 'layer')
    return layer

def create_sublayer(label):
    sublayer = ET.Element(f'{{{SVG_NS}}}g')
    sublayer.set(f'{{{INKSCAPE_NS}}}label', label)
    return sublayer

def create_circle(coords, label, style):
    cx, cy = coords
    circle = ET.Element(f'{{{SVG_NS}}}circle')
    circle.set('cx', str(cx))
    circle.set('cy', str(cy))
    circle.set('r', str(style["diameter"] / 2))
    fill = style.get("fill", "white") or "white"  # Ensure not None
    circle.set('fill', fill)
    circle.set('stroke', "black")
    circle.set('stroke-width', str(style["stroke"]))
    circle.set('id', str(label))
    return circle

def create_text(coords, label, style):
    x, y = coords
    text = ET.Element(f'{{{SVG_NS}}}text')
    text.set('x', str(x + 0.1))
    text.set('y', str(y - 0.1))
    font_size = style['font_size']
    font_style = style.get('font_style', 'normal') or 'normal'
    font_weight = 'bold' if font_style == 'bold' else 'normal'
    font_style_attr = 'italic' if font_style == 'italic' else 'normal'
    fill = style.get('fill', '#000000') or '#000000'
    text.set('style', f"font-size:{font_size}pt;font-family:Arial;font-style:{font_style_attr};font-weight:{font_weight};fill:{fill}")
    content = str(label).upper() if style.get("uppercase") else str(label)
    tspan = ET.Element(f'{{{SVG_NS}}}tspan')
    tspan.text = content
    text.append(tspan)
    return text

# --- MAIN EXECUTION ---
if not os.path.exists(SVG_FILE) or not os.path.exists(GEOJSON_FILE):
    raise FileNotFoundError("SVG or GeoJSON file not found.")

tree = ET.parse(SVG_FILE)
root = tree.getroot()

with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
    geojson = json.load(f)

# Remove existing layers if present
for layer in root.findall(f".//{{{SVG_NS}}}g[@inkscape:label='{SETTLEMENT_LAYER_NAME}']", namespaces={'inkscape': INKSCAPE_NS}):
    root.remove(layer)
for layer in root.findall(f".//{{{SVG_NS}}}g[@inkscape:label='{DISPLAY_LABEL_LAYER_NAME}']", namespaces={'inkscape': INKSCAPE_NS}):
    root.remove(layer)

icons_layer = create_layer(SETTLEMENT_LAYER_NAME)
labels_layer = create_layer(DISPLAY_LABEL_LAYER_NAME)

# Organize sublayers by province
icon_sublayers = {}
label_sublayers = {}

for feature in geojson["features"]:
    props = feature["properties"]
    coords = feature["geometry"]["coordinates"]
    name = props["name"]
    province = props["province"]
    population = props.get("population")
    try:
        pop = int(population) if population is not None else None
    except ValueError:
        pop = None

    style = get_style_for_population(pop)

    # Icons
    if province not in icon_sublayers:
        icon_sublayers[province] = create_sublayer(province)
        icons_layer.append(icon_sublayers[province])
    circle = create_circle(coords, name, style)
    icon_sublayers[province].append(circle)

    # Labels
    if province not in label_sublayers:
        label_sublayers[province] = create_sublayer(province)
        labels_layer.append(label_sublayers[province])
    text = create_text(coords, name, style)
    label_sublayers[province].append(text)

root.append(icons_layer)
root.append(labels_layer)

tree.write(SVG_FILE)
print("✅ SVG updated with settlement icons and display labels.")
