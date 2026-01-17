---
applyTo: "**/*.py"
---
# Project coding standards for Python
- Follow the PEP 8 style guide for Python.
- Always prioritize readability and clarity.
- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Place all newly created python scripts in the "oldworldatlas-tools/scripts/" directory unless there is a specific reason to place them elsewhere.

- Keep in mind that all SVG files are saved as Inkscape SVG files 
- Use one consistent package for parsing SVG files, either `xml.etree.ElementTree`, `lxml`, `svgelements` or `svgpathtools` depending on which package is the most suitable for the project requirements. Stay consistent throughout the codebase, and refactor existing code or go back and rewrite using the chosen package if necessary.

- Do not save any changes to the SVG files unless explicitly instructed to do so.
- When converting from the SVG coordinate system to a Cartesian coordinate system, stay consistent with the chosen method and scaling factors throughout the codebase, so that settlements, points of interest, lines, shapes, and other elements are accurately represented in the Cartesian system and relative to each other.
- A small number of larger files, or a smaller number of more modular files? Consider the pros and cons of each approach when adding new functionality or refactoring existing code. Consider also some routines, for example extracting and updating settlements from the root SVG file will be performed often, practically every time the map is updated. Make it user friendly with readable instructions.