---
agent: agent
model: Claude Haiku 4.5 (copilot)
description: Process and analyze information from an .svg map file to extract relevant data, clean data and populate databases.
tools: ['vscode', 'execute', 'read', 'edit', 'search', 'web', 'agent', 'pylance-mcp-server/*', 'ms-python.python/getPythonEnvironmentInfo', 'ms-python.python/getPythonExecutableCommand', 'ms-python.python/installPythonPackage', 'ms-python.python/configurePythonEnvironment', 'ms-toolsai.jupyter/configureNotebook', 'ms-toolsai.jupyter/listNotebookPackages', 'ms-toolsai.jupyter/installNotebookPackages', 'todo']

---
The objective is to create a set of files which will process and analyze information from an .svg map file to extract relevant data, clean data and populate databases. Specifically:

SVG maps are found in the directory: "C:\Users\toddc\dev\personal\old-world-atlas\oldworldatlas-maps". For now the focus will be on the file "SETTLEMENTS_POI_ROADS.svg" which contains information about settlements, points of interest and roads in the following format:

Top level layer "Settlements" contains sub-layers for each political faction named after each factions: "Kislev", "Bretonnia", "Empire", etc. For now, focus exclusively on "Empire". "Empire" layer contains multiple layers for each province:
- "Averland"
- "Hochland"
- "Middenland"
- "Mootland"
- "Nordland"
- "Ostland"
- "Reikland"
- "Stirland"
- "Talabecland"
- "Wissenland"

Each province layer contains settlements as individual SVG textbox elements with labels and text content (tspan), which should be both identically the name of the settlement, and coordinates (x,y) attributes representing their location on the map. 

As a sanity check, the settlements: 
"Altdorf" should be found in "Reikland" at SVG coordinates x="429.058" and y = "408.152" and geographic coordinates of longitude: 0.007 latitude: 51.465

"Middenheim" should be found in "Middenland" at SVG coordinates x="495.263" and y="187.911" and geographic coordinates of longitude: 1.167 latitude: 55.318

"Wachdorf" should be in "Averland" at SVG coordinates x="738.171" and y="778.741" and geographic coordinates of longitude: 5.421 latitude: 44.977

There should be multiple settlements called "Waldenhof" but the one in "Stirland" should be at SVG coordinates x="891.383" and y="479.367" and geographic coordinates of longitude: 8.100 latitude: 50.219

These numbers may be slightly rounded or off by a small margin of error, but should be very close. Use them to form the basis of the scaling between coordinate systems, transforming SVG coordinates to geographic coordinates. This transformation should be consistent across the entire map, so that all settlements, points of interest, roads, and other elements are accurately represented in the Cartesian system and relative to each other.


Include a routine that checks that each element in the province layers is indeed a textbox element with a label matching the text content (which is the settlement name and should not be empty). If any elements are found that do not match this criteria, log them to a separate file "invalid_settlement_elements.log" with details of the province layer they were found in and their SVG attributes for further manual review.

Check also that there are no duplicate settlement names within each province layer. If duplicates are found, log them to a separate file "duplicate_settlements.log" with details of the province layer they were found in and their SVG attributes for further manual review. Identical names are allowed across different provinces, but not within the same province.

Information on the population sizes of each settlement can be found in the files data/The-Empire/*.csv where * is the province name, e.g. "data/The-Empire/reikland.csv". Each CSV file contains a "Settlement" column and a "Population" column which can be used to look up the population of each settlement. There is no header or column names. Send an alert/notification if a settlement is found in the CSV file without a corresponding settlement in the SVG file. In the reverse case, if a settlement is found in the SVG file without a corresponding entry in the CSV file, set the population to a random value between 100 and 800. Consider using a log-normal distribution to generate these random populations to better reflect real-world population distributions. Make it so that this function can be re-run if the CSV files are updated in the future, and it will update the populations accordingly.

Assign a size category to each settlement based on its population using the following scale:
- Hamlet (1): 1-300
- Village (2): 301-2000
- Town (3): 2001-9000
- City (4): 9001-20000
- Large City (5): 20001 and above

Finally, compile all this information into a GeoJSON file representing all settlements in the "Empire" faction.
The final output should be a file "empire_settlements.geojson" which has the following structure:
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [
          1.81359656818836,     ## Longitude from conversion
          47.92166546609956     ## Latitude from conversion
        ]
      },
      "properties": {
        "name": "Heves",
        "province": "Averland",  ## Corresponding province layer
        "population": 121,       ## Randomly assigned, not found in CSV
        "notes": [],            # Empty for all settlements for now
        "size_category": 1,      ## Based on population
        "inkscape_coordinates": [    ## Original SVG coordinates
          533.0741,
          610.31311
        ]
      }
    },
...

Perform all of the above also for "Westerland" faction, creating a separate GeoJSON file "westerland_settlements.geojson" with identical structure and processing steps. The "Westerland" faction has no provinces, so leave the province property as an empty string for all settlements in that faction. Westerland settlements can be found in the top level layer "Settlements" under the sublayer "Westerland". Population data for Westerland settlements can be found in the file "data/Westerland/westerland.csv" with identical structure to the Empire CSV files.

Perform a similar treatment for all the textbox elements in the top level layer "Points of Interest", which contain sublayers divided not by province, but by type:
- "Other"
- "City Districts"
- "Forts and Castles"
- "Monasteries and Temples"
- "Taverns and Inns"
These points are structured in the SVG identically to the settlements, with each point represented as a textbox element with label and tspan text content representing the name of the point of interest, and x,y attributes representing their location on the map. 

Compile all this information into a GeoJSON file (with converted, georeferenced coordinates) representing all points of interest with the following properties for each point of interest:
- name
- type (corresponding to the sublayer they were found in)
- inkscape_coordinates (original SVG coordinates as an array [x,y])



Perform a similar treatment for all the line elements in the top level layer "Roads", which contain multiple sublayers for different road types:
- "Imperial Highways"
- "Roads"
- "Paths"
For now, there are only SVG line elements in "Imperial Highways" - you can expect "Roads" and "Paths" to be empty for now. Create a GeoJSON file "empire_roads.geojson" with the following structure for each road:
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [longitude1, latitude1],
          [longitude2, latitude2],
          ...
        ]
      },
      "properties": {
        "road_type": "Imperial Highways",  ## Corresponding sublayer
        "road_id": "road_001",              ## Unique identifier for the road
        "inkscape_coordinates": [          ## Original SVG coordinates as an array of [x,y] pairs
          [x1, y1],
          [x2, y2],
          ...
        ]
      }
    },

The roads are hand-drawn and include Bezier curves, so a method for accurately sampling points along these curves will be needed to convert them into a series of longitude and latitude coordinates for the GeoJSON output.

Finally, as confirmation, generate a summary report "processing_report.txt" which includes:
- Total number of settlements processed for each faction (Empire and Westerland)
- the total population across all settlements for each province and faction
- Total number of invalid settlement elements found
- Total number of points of interest processed
- Total number of roads processed
- the total number of coordinate points generated for all roads combined
- Any anomalies or issues encountered during processing, such as missing population data or unexpected SVG structures.


If any instructions are unclear or contradictory, ask for clarification before proceeding.