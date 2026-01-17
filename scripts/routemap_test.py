import itertools
import math

import networkx as nx
import numpy as np
from lxml import etree
from shapely.geometry import LineString, Point
from svgpathtools import parse_path
from shapely.ops import nearest_points



# =========================
# Configuration
# =========================
class NodeRegistry:
    def __init__(self, tol):
        self.tol = tol
        self.nodes = {}     # id -> Point
        self.next_id = 0

    def get(self, pt: Point):
        for nid, p in self.nodes.items():
            if p.distance(pt) <= self.tol:
                return nid
        nid = self.next_id
        self.nodes[nid] = pt
        self.next_id += 1
        return nid


SVG_FILE = r"c:\Users\Todd Kozlowski\python_projects\empire_map\testmap.svg"

SETTLEMENT_LAYER = "settlements"
ROAD_LAYER = "roads"

JUNCTION_TOL = 10.0
NODE_MERGE_TOL = 0.7 # slightly more than 0.5 * SAMPLE_STEP_PX

PX_TO_KM = 2.44 / 3.76      # given scale
SAMPLE_STEP_PX = 1.0        # densify roads
MM_TO_KM = 2.44             # mm to km at given scale


SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"


# =========================
# SVG helpers
# =========================

def get_layer(tree, label):
    return tree.xpath(
        f".//svg:g[@inkscape:label='{label}']",
        namespaces={"svg": SVG_NS, "inkscape": INKSCAPE_NS}
    )[0]


def parse_settlements(tree):
    layer = get_layer(tree, SETTLEMENT_LAYER)
    settlements = {}

    for t in layer.findall(f".//{{{SVG_NS}}}text"):
        tspan = t.find(f".//{{{SVG_NS}}}tspan")
        if tspan is None or tspan.text is None:
            continue

        name = tspan.text.strip()

        # Inkscape text position = bottom-left
        x = float(t.attrib["x"])
        y = float(t.attrib["y"])

        settlements[name] = Point(x, y)

    return settlements


def parse_roads(tree):
    layer = get_layer(tree, ROAD_LAYER)
    paths = []

    for p in layer.findall(f".//{{{SVG_NS}}}path"):
        paths.append(parse_path(p.attrib["d"]))

    # if len(paths) != 2:
    #     raise RuntimeError("This script assumes exactly two roads")

    return paths

def dist_km(p1: Point, p2: Point):
    return p1.distance(p2) * MM_TO_KM


# =========================
# Geometry helpers
# =========================

def path_to_linestring(path):
    length = path.length()
    n = max(int(length / SAMPLE_STEP_PX), 2)

    pts = [
        path.point(i / (n - 1))
        for i in range(n)
    ]

    coords = [(p.real, p.imag) for p in pts]
    return LineString(coords)


# =========================
# Graph construction
# =========================

def build_graph(roads, settlements, junction):
    """
    roads: list[LineString]
    settlements: dict[name -> Point]
    junction: Point
    """


    G = nx.Graph()
    registry = NodeRegistry(NODE_MERGE_TOL)

    # --------------------------------------------------
    # 1. FORCE ALL ROADS THROUGH THE JUNCTION
    # --------------------------------------------------

    snapped_roads = []

    for road in roads:
        coords = []
        for x, y in road.coords:
            p = Point(x, y)
            if p.distance(junction) <= JUNCTION_TOL:
                coords.append((junction.x, junction.y))
            else:
                coords.append((x, y))
        snapped_roads.append(coords)

    # --------------------------------------------------
    # 2. ADD ROAD BACKBONE
    # --------------------------------------------------

    for coords in snapped_roads:
        for a, b in zip(coords[:-1], coords[1:]):
            pa = Point(a)
            pb = Point(b)

            na = registry.get(pa)
            nb = registry.get(pb)

            G.add_edge(na, nb, weight=dist_km(pa, pb))

    # --------------------------------------------------
    # 3. SNAP SETTLEMENTS TO ROADS
    # --------------------------------------------------

    road_union = None
    for r in roads:
        road_union = r if road_union is None else road_union.union(r)

    settlement_nodes = {}

    for name, sp in settlements.items():
        rp = nearest_points(road_union, sp)[0]

        nr = registry.get(rp)
        ns = registry.get(sp)

        G.add_edge(ns, nr, weight=dist_km(sp, rp))
        settlement_nodes[name] = ns

    # --------------------------------------------------
    # 4. FINAL SANITY CHECK
    # --------------------------------------------------

    comps = list(nx.connected_components(G))
    print(f"Connected components: {len(comps)}")
    if len(comps) != 1:
        raise RuntimeError("Graph is not fully connected")

    return G, settlement_nodes

def settlement_distances(G, settlement_nodes):
    names = list(settlement_nodes.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = names[i]
            b = names[j]
            na = settlement_nodes[a]
            nb = settlement_nodes[b]

            d = nx.shortest_path_length(G, na, nb, weight="weight")
            print(f"{a} -> {b}: {d:.2f} km")

            
def find_road_junction(roads, tol):
    best_dist = float("inf")
    best_point = None

    for i in range(len(roads)):
        for j in range(i + 1, len(roads)):
            p1, p2 = nearest_points(roads[i], roads[j])
            d = p1.distance(p2)
            if d < best_dist:
                best_dist = d
                best_point = Point(
                    (p1.x + p2.x) / 2,
                    (p1.y + p2.y) / 2
                )
    
    print(f"Best junction gap found: {best_dist:.4f} (tolerance: {tol})")

    if best_dist > tol:
        raise RuntimeError(f"No road junction found (closest gap {best_dist} > {tol})")

    return best_point


# =========================
# Main
# =========================

def main():
    tree = etree.parse(SVG_FILE)

    settlements = parse_settlements(tree)
    raw_roads = parse_roads(tree)
    
    # Convert SVG paths to LineString
    roads = [path_to_linestring(p) for p in raw_roads]
    
    junction = find_road_junction(roads, JUNCTION_TOL)
    G, settlement_nodes = build_graph(roads, settlements, junction)

    print("Connected components:", nx.number_connected_components(G))

    print("\nPairwise settlement distances (km):\n")
    for a, b in itertools.combinations(settlement_nodes.keys(), 2):
        na = settlement_nodes[a]
        nb = settlement_nodes[b]
        d = nx.shortest_path_length(G, na, nb, weight="weight")
        print(f"{a} <-> {b}: {d:.2f} km")


if __name__ == "__main__":
    main()
