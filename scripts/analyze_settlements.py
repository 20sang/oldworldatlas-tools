import json
from collections import defaultdict, Counter

# Path to your GeoJSON file
geojson_path = "settlements.geojson"

# Load GeoJSON
with open(geojson_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Initialize
province_counts = defaultdict(int)
province_populations = defaultdict(int)
name_counts = Counter()
name_provinces = defaultdict(list)

# Parse features
for feature in data["features"]:
    props = feature.get("properties", {})
    name = props.get("name", "").strip()
    province = props.get("province", "Unknown").strip()
    population = props.get("population")
    if population == 0:
        population = 100

    if name:
        name_counts[name] += 1
        name_provinces[name].append(province)

    province_counts[province] += 1
    if isinstance(population, int) and population > 0:
        province_populations[province] += population

# Output: number of settlements per province
print("Settlements per province:")
for province, count in sorted(province_counts.items()):
    print(f"  {province}: {count} settlements, {province_populations[province]} population in settlements")
print('Total settlements:', sum(province_counts.values()))
print('Total population in settlements:', sum(province_populations.values()))

# Output: duplicates with province list
duplicates = {name: provs for name, provs in name_provinces.items() if len(provs) > 1}
if duplicates:
    print("\nDuplicate settlement names found:")
    for name, provinces in sorted(duplicates.items()):
        province_list = ", ".join(provinces)
        print(f"  {name} ({province_list})")
else:
    print("\nNo duplicate settlement names found.")
