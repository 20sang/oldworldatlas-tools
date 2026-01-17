import xml.etree.ElementTree as ET
import json
import os
import csv
import map_classes
import pandas as pd

svg_path = r"E:\Maps\the_old_world_SETTLEMENTS_POI_ROADS.svg"
empire_gazetteer_path = r"E:\Maps\gazetteers\The Empire"
geojson_path = "settlements.geojson"
ns = {
        'svg': 'http://www.w3.org/2000/svg',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
    }
nations = {
    "bretonnia": ".//svg:g[@inkscape:label='Settlements']/svg:g[@inkscape:label='Bretonnia']",
    "the_empire": ".//svg:g[@inkscape:label='Settlements']/svg:g[@inkscape:label='The Empire']",
    "tilea": ".//svg:g[@inkscape:label='Settlements']/svg:g[@inkscape:label='Tilea']",
    "estalia": ".//svg:g[@inkscape:label='Settlements']/svg:g[@inkscape:label='Estalia']",
}
provinces = {
    "averland": nations["the_empire"] + "/svg:g[@inkscape:label='Averland']",
    "hochland": nations["the_empire"] + "/svg:g[@inkscape:label='Hochland']",
    "middenland": nations["the_empire"] + "/svg:g[@inkscape:label='Middenland']",
    "mootland": nations["the_empire"] + "/svg:g[@inkscape:label='Mootland']",
    "nordland": nations["the_empire"] + "/svg:g[@inkscape:label='Nordland']",
    "ostermark": nations["the_empire"] + "/svg:g[@inkscape:label='Ostermark']",
    "ostland": nations["the_empire"] + "/svg:g[@inkscape:label='Ostland']",
    "reikland": nations["the_empire"] + "/svg:g[@inkscape:label='Reikland']",
    "stirland": nations["the_empire"] + "/svg:g[@inkscape:label='Stirland']",
    "talabecland": nations["the_empire"] + "/svg:g[@inkscape:label='Talabecland']",
    "wissenland": nations["the_empire"] + "/svg:g[@inkscape:label='Wissenland']",
}

_change_flag = False #indicates if changes to the svg have been made and need to be saved
tree = ET.parse(svg_path)
root = tree.getroot()
xml_settlement_group = root.find(".//svg:g[@inkscape:label='Settlements']", ns)
total_settlement_count = len(xml_settlement_group.findall(".//svg:text", ns))
print(f"Total settlements found in SVG: {total_settlement_count}")

def conform_label_to_text_content(settlement_element):
    # routine to compare the label (if one exists) to the text content, and change (or create) the label to match the text content
    text_label = settlement_element.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label')
    # check if the element has a text attribute, if not, return the current label and skip
    if settlement_element.find(".//{http://www.w3.org/2000/svg}tspan") is None:
        print(f"Settlement element {settlement_element.attrib.get('id')} has no text content.")
        return None
    else:
        text_content = settlement_element.find(".//{http://www.w3.org/2000/svg}tspan").text
    if text_content and text_label != text_content:
        print(f"Updating label from '{text_label}' to '{text_content}'")
        settlement_element.set('{http://www.inkscape.org/namespaces/inkscape}label', text_content)
        global _change_flag
        _change_flag = True
    return settlement_element.get('{http://www.inkscape.org/namespaces/inkscape}label')

def create_settlement_object(settlement_element, province):
    name = conform_label_to_text_content(settlement_element)
    if not name:
        print(settlement_element.attrib.get('id'))
        print(ET.tostring(settlement_element, encoding='unicode'))
        print(settlement_element.find(".//{http://www.w3.org/2000/svg}tspan").text)
        raise ValueError("Settlement element has no name or text content.")
    x = float(settlement_element.get('x')) + 3.0
    y = float(settlement_element.get('y')) + 4.0
    return map_classes.Settlement(name=name, province=province, x=x, y=y)

def flag_identically_named_settlements(settlement_objects):
    # see if any two settlements share both name and province, and if so, 
    # flag them for manual review
    name_province_count = {}
    for settlement in settlement_objects:
        key = (settlement.name, settlement.province)
        if key in name_province_count:
            name_province_count[key] += 1
        else:
            name_province_count[key] = 1
    duplicates = {key: count for key, count in name_province_count.items() if count > 1}
    if duplicates:
        print("Warning: The following settlements have identical names and provinces:")
        for (name, province), count in duplicates.items():
            print(f" - {name} in {province}: {count} occurrences")
    return duplicates

def get_population_from_csv(settlement_object):
    # routine to get the population of a settlement from a CSV file
    # and assign it to the settlement object. If a matching settlement
    # is not found, set the population to zero. There is a unique CSV for
    # each province, all found a directory 'gazetteer' in the same directory
    # as the SVG file.
    csv_dir = empire_gazetteer_path
    csv_file = os.path.join(csv_dir, f"{settlement_object.province}.csv")
    if not os.path.exists(csv_file):
        #print(f"No CSV file found for province: {settlement_object.province}")
        settlement_object.population = 0
        return
    name, population = pd.read_csv(csv_file, header=None).values.T
    df = pd.DataFrame({'name': name, 'population': population})
    match = df[df['name'].str.lower() == settlement_object.name.lower()]
    if not match.empty:
        settlement_object.population = int(match.iloc[0]['population'])
        #print(f"Assigned population {settlement_object.population} to {settlement_object.province} : {settlement_object.name}")
    else:
        #print(f"No population data for {settlement_object.name} in {settlement_object.province}")
        settlement_object.population = 0       

def check_unassigned_csv_settlements(province):
    # function to check to see if every settlement in the CSV has a matching settlement in the SVG
    # and if not, inform the user which settlements in the CSV were not found in the SVG
    csv_dir = empire_gazetteer_path
    csv_file = os.path.join(csv_dir, f"{province}.csv")
    if not os.path.exists(csv_file):
        print(f"No CSV file found for province: {province} at {csv_file}")
        return
    name, population = pd.read_csv(csv_file, header=None).values.T
    df = pd.DataFrame({'name': name, 'population': population})
    svg_settlements = [s for s in settlement_objects if s.province.lower() == province.lower()]
    svg_names = [s.name.lower() for s in svg_settlements]
    missing = df[~df['name'].str.lower().isin(svg_names)]
    if not missing.empty:
        print(f"The following settlements from {province}.csv were not found in the SVG:")
        for name in missing['name']:
            print(f" - {name}")

def update_geojson(settlement_objects, geojson_path):
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson = json.load(f)
    else:
        geojson = {"type": "FeatureCollection", "features": []}

    existing_features = {
        (f["properties"]["name"], f["properties"]["province"]): f
        for f in geojson.get("features", [])
        if f["properties"].get("name") and f["properties"].get("province")
    }

    for settlement in settlement_objects:
        key = (settlement.name, settlement.province)
        if key in existing_features:
            feature = existing_features[key]
            feature["geometry"]["coordinates"] = [settlement.x, settlement.y]
            feature["properties"]["population"] = settlement.population  # Ensure population is updated
            feature["properties"]["name"] = settlement.name
            feature["properties"]["province"] = settlement.province
            feature["properties"]["notes"] = settlement.notes
            #print(f"Updated existing feature: {settlement.name} in {settlement.province}")
        else:
            new_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [settlement.x, settlement.y]
                },
                "properties": {
                    "name": settlement.name,
                    "province": settlement.province,
                    "population": settlement.population
                }
            }
            geojson["features"].append(new_feature)
            print(f"Added new feature: {settlement.name} in {settlement.province}")

    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"GeoJSON data saved to {geojson_path}")

settlement_objects = []

for province in provinces.keys():
    province_settlements = root.find(provinces[province], ns)
    if province_settlements is not None:
        xml_settlements = province_settlements.findall(".//svg:text", ns)
        for settlement in xml_settlements:
            settlement_obj = create_settlement_object(settlement, province=province.title())
            settlement_objects.append(settlement_obj)
            if os.path.exists(os.path.join(empire_gazetteer_path, f"{province}.csv")):
                get_population_from_csv(settlement_obj)
            #print(f"Created settlement: {settlement_obj.name} in {settlement_obj.province} at ({settlement_obj.x}, {settlement_obj.y})")
        update_geojson(settlement_objects, geojson_path)
        if os.path.exists(os.path.join(empire_gazetteer_path, f"{province}.csv")):
            check_unassigned_csv_settlements(province)
    else:
        print(f"No settlements found for province: {province}")
flag_identically_named_settlements(settlement_objects)
print("Processing complete.")

print(f"Total settlements processed: {len(settlement_objects)}")
# Save changes to the SVG file
if _change_flag:
    print("Changes were made to the SVG file. Saving updates...")
    tree.write(svg_path)
else:
    print("No changes were made to the SVG file. No need to save.")