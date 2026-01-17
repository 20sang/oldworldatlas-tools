import sys
from lxml import etree
from svgpathtools import parse_path
from shapely.geometry import Point

SVG_FILE = r"c:\Users\Todd Kozlowski\python_projects\empire_map\testmap.svg"
SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

def get_layer(tree, label):
    return tree.xpath(
        f".//svg:g[@inkscape:label='{label}']",
        namespaces={"svg": SVG_NS, "inkscape": INKSCAPE_NS}
    )[0]

def main():
    try:
        tree = etree.parse(SVG_FILE)
        roads_layer = get_layer(tree, "roads")
        paths = []
        for p in roads_layer.findall(f".//{{{SVG_NS}}}path"):
            paths.append(parse_path(p.attrib["d"]))
        
        print(f"Found {len(paths)} paths.")
        for i, path in enumerate(paths):
            start = path.point(0)
            end = path.point(1)
            print(f"Path {i}: Start({start.real:.2f}, {start.imag:.2f}), End({end.real:.2f}, {end.imag:.2f})")
            
        # Check settlements
        settlement_layer = get_layer(tree, "settlements")
        texts = settlement_layer.findall(f".//{{{SVG_NS}}}text")
        print(f"Found {len(texts)} settlements.")
        for t in texts:
             tspan = t.find(f".//{{{SVG_NS}}}tspan")
             if tspan is not None and tspan.text:
                 print(f"Settlement: {tspan.text.strip()} at ({t.attrib['x']}, {t.attrib['y']})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
