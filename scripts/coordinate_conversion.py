import json
import math
import numpy as np
from pathlib import Path

def categorize_population(population):
    """Categorize settlements by population size."""
    # Handle NaN, None, or missing values
    if population is None or (isinstance(population, float) and math.isnan(population)):
        return 1
    
    try:
        pop = float(population)
    except (ValueError, TypeError):
        return 1
    
    if pop < 200:
        return 1
    elif pop <= 800:
        return 2
    elif pop <= 2000:
        return 3
    elif pop <= 7500:
        return 4
    elif pop <= 15000:
        return 5
    else:
        return 6

def compute_affine_transform():
    """
    Compute affine transformation from Inkscape coordinates to Lon/Lat.
    
    Reference points:
    Point 1: (1.1675, 55.318) = (496.038, 178.482)
    Point 2: (7.457, 53.477) = (854.951, 292.844)
    Point 3: (-2.656, 53.361) = (276.97, 299.81)
    
    Where first pair is (lon, lat) and second pair is (inkscape_x, inkscape_y)
    
    Linear transformation using least squares fitting:
    lon = a * x + b * y + c
    lat = d * x + e * y + f
    """
    # Reference points in Inkscape coordinates (x, y)
    A = np.array([
        [495.263, 187.912, 1],
        [854.951, 292.844, 1],
        [276.97, 299.81, 1]
    ])
    
    # Corresponding Lon/Lat values
    lonlat_points = np.array([
        [1.1675, 55.318],
        [7.457, 53.477],
        [-2.656, 53.361]
    ])
    
    # Solve for longitude transformation using least squares: lon = a*x + b*y + c
    lon_coeffs, _, _, _ = np.linalg.lstsq(A, lonlat_points[:, 0], rcond=None)
    
    # Solve for latitude transformation using least squares: lat = d*x + e*y + f
    lat_coeffs, _, _, _ = np.linalg.lstsq(A, lonlat_points[:, 1], rcond=None)
    
    return lon_coeffs, lat_coeffs

def convert_inkscape_to_lonlat(inkscape_x, inkscape_y, lon_coeffs, lat_coeffs):
    """Convert Inkscape coordinates to Lon/Lat using affine transformation."""
    lon = lon_coeffs[0] * inkscape_x + lon_coeffs[1] * inkscape_y + lon_coeffs[2]
    lat = lat_coeffs[0] * inkscape_x + lat_coeffs[1] * inkscape_y + lat_coeffs[2]
    return [lon, lat]

def process_settlements():
    """Load settlements, add properties, and save georeferenced version."""
    # Load settlements.geojson
    input_file = Path(__file__).parent / 'settlements.geojson'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    # Compute transformation coefficients
    lon_coeffs, lat_coeffs = compute_affine_transform()
    
    # Process each feature
    for feature in geojson_data['features']:
        properties = feature['properties']
        geometry = feature['geometry']
        
        # Add size_category based on population
        population = properties.get('population')
        properties['size_category'] = categorize_population(population)
        
        # Store original Inkscape coordinates
        if geometry['type'] == 'Point':
            original_coords = geometry['coordinates'].copy()
            properties['inkscape_coordinates'] = original_coords
            
            # Convert Inkscape coordinates to Lon/Lat
            inkscape_x, inkscape_y = original_coords
            lonlat_coords = convert_inkscape_to_lonlat(inkscape_x, inkscape_y, lon_coeffs, lat_coeffs)
            
            # Replace geometry coordinates with converted values
            geometry['coordinates'] = lonlat_coords
    
    # Save the georeferenced geojson
    output_file = Path(__file__).parent / 'settlements_georeferenced.geojson'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2)
    
    print(f"Successfully processed {len(geojson_data['features'])} settlements")
    print(f"Georeferenced file saved to: {output_file}")
    
    # Print some sample data to verify
    print("\nSample conversions:")
    for i, feature in enumerate(geojson_data['features'][:3]):
        props = feature['properties']
        orig = props.get('inkscape_coordinates')
        new = feature['geometry']['coordinates']
        print(f"  Settlement: {props.get('name', 'Unknown')}")
        print(f"    Population: {props.get('population')}, Size Category: {props.get('size_category')}")
        print(f"    Inkscape: {orig} → Lon/Lat: {new}")

if __name__ == '__main__':
    process_settlements()
