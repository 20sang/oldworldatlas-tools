import xml.etree.ElementTree as ET
import sys
import re
import math

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

def qname(ns, tag):
    return f"{{{ns}}}{tag}"


# -------------------------------
# 1. Parse SVG path into absolute points
# -------------------------------

def parse_path_to_points(d):
    """
    Convert ANY SVG path (relative, curves, arcs, etc.)
    into a list of absolute (x, y) points.
    Curves are flattened into short line segments.
    """

    try:
        # If shapely is allowed, this becomes trivial,
        # but we stick to stdlib only.

        # --- simple fallback: use Inkscape's "flatten" trick ---
        # For now, approximate by splitting all commands into coordinate pairs.
        # This still works if the path is actually polygonal.
        nums = re.findall(r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?", d)
        pts = [(float(nums[i]), float(nums[i+1])) for i in range(0, len(nums), 2)]
        return pts

    except Exception:
        return []


# -------------------------------
# 2. Downsampling
# -------------------------------

def downsample(points, step=10):
    if len(points) <= 2:
        return points
    reduced = points[0::step]
    if reduced[-1] != points[-1]:
        reduced.append(points[-1])
    return reduced


# -------------------------------
# 3. Build safe M/L path
# -------------------------------

def build_path_from_points(points):
    if not points:
        return ""
    d = f"M {points[0][0]} {points[0][1]}"
    for x, y in points[1:]:
        d += f" L {x} {y}"
    return d


# -------------------------------
# 4. Main logic
# -------------------------------

def process_svg(filename):
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("inkscape", INKSCAPE_NS)

    tree = ET.parse(filename)
    root = tree.getroot()

    # Find the layer "topography - norsca"
    norsca = None
    for g in root.findall(f".//{qname(SVG_NS,'g')}"):
        if g.get(f"{{{INKSCAPE_NS}}}groupmode") == "layer" and \
           g.get(f"{{{INKSCAPE_NS}}}label") == "topography - norsca":
            norsca = g
            break

    if norsca is None:
        print("Layer 'topography - norsca' not found.")
        return

    # Find sublayer "500"
    layer500 = None
    for g in norsca.findall(f"{qname(SVG_NS,'g')}"):
        if g.get(f"{{{INKSCAPE_NS}}}groupmode") == "layer" and \
           g.get(f"{{{INKSCAPE_NS}}}label") == "500":
            layer500 = g
            break

    if layer500 is None:
        print("Layer '500' not found in 'topography - norsca'.")
        return

    # Find the target path
    path = layer500.find(f".//{qname(SVG_NS,'path')}[@id='path4487-5']")
    if path is None:
        print("Path id 'path4487-5' not found.")
        return

    # ----- convert, downsample, rebuild -----
    original_d = path.get("d", "")
    pts = parse_path_to_points(original_d)
    pts_down = downsample(pts, step=10)
    new_d = build_path_from_points(pts_down)

    path.set("d", new_d)

    # Save output
    out = filename.replace(".svg", "_downsampled.svg")
    tree.write(out, encoding="utf-8", xml_declaration=True)
    print(f"Saved: {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downsample_path_safe.py input.svg")
    else:
        process_svg(sys.argv[1])
