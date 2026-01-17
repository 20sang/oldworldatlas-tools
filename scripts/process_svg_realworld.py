import xml.etree.ElementTree as ET
import re
import sys

def count_path_nodes(d_attr):
    """Estimate number of coordinate pairs (nodes) in an SVG path string."""
    coords = re.findall(r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?", d_attr)
    return len(coords) // 2


def process_svg(filename):
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")

    tree = ET.parse(filename)
    root = tree.getroot()

    SVG_NS = "http://www.w3.org/2000/svg"
    INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

    def qname(ns, tag):
        return f"{{{ns}}}{tag}"

    # Find the layer named "realworld topography"
    topo_layer = None
    for g in root.findall(f".//{qname(SVG_NS,'g')}"):
        if (
            g.get(f"{{{INKSCAPE_NS}}}groupmode") == "layer"
            and g.get(f"{{{INKSCAPE_NS}}}label") == "realworld_greece"
        ):
            topo_layer = g
            break

    if topo_layer is None:
        print("Layer 'realworld topography' not found.")
        return

    # Iterate through the groups (make a copy list to modify safely)
    groups = list(topo_layer.findall(f"{qname(SVG_NS,'g')}"))

    for i, group in enumerate(groups):
        group_label = group.get(f"{{{INKSCAPE_NS}}}label") or group.get("id", "unnamed")

        # Create a new layer element with same name
        new_layer = ET.Element(
            qname(SVG_NS, 'g'),
            {
                f"{{{INKSCAPE_NS}}}groupmode": "layer",
                f"{{{INKSCAPE_NS}}}label": group_label,
                "id": f"layer_{group_label}",
            }
        )

        # Move paths from the group into new layer
        for path in list(group.findall(f"{qname(SVG_NS,'path')}")):
            new_layer.append(path)

        # Replace the group with the new layer (preserving order)
        idx = list(topo_layer).index(group)
        topo_layer.remove(group)
        topo_layer.insert(idx, new_layer)

    # Now, remove paths with <= 4 nodes from these numeric layers
    for lyr in topo_layer.findall(f"{qname(SVG_NS,'g')}"):
        if lyr.get(f"{{{INKSCAPE_NS}}}groupmode") == "layer":
            label = lyr.get(f"{{{INKSCAPE_NS}}}label", "")
            if label.isdigit():  # only numeric layers
                for path in list(lyr.findall(f"{qname(SVG_NS,'path')}")):
                    d = path.get("d", "")
                    if count_path_nodes(d) <= 4:
                        lyr.remove(path)

    # Save result
    outname = filename.replace(".svg", "_processed.svg")
    tree.write(outname, encoding="utf-8", xml_declaration=True)
    print(f"Saved processed SVG as {outname}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_svg_layers_etree.py input.svg")
    else:
        process_svg(sys.argv[1])
