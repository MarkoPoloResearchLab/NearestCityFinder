#!/usr/bin/env python3

import argparse
import sys
import tempfile
from typing import Dict, List, Tuple, Optional
import googlemaps
from flask import Flask, render_template, request, redirect, url_for
from config import GOOGLE_MAPS_API_KEY
from utils import (
    read_cities_file,
    geocode_city,
    haversine_distance,
    get_driving_distance
)

app = Flask(__name__)

def parse_arguments() -> Optional[argparse.Namespace]:
    """Parse command line arguments."""
    if len(sys.argv) == 1:  # No command line arguments, running as web app
        return None

    parser = argparse.ArgumentParser(
        description='Find the closest city by driving distance within a specified radius'
    )
    parser.add_argument(
        '-f', '--file',
        required=True,
        help='Path to text file containing list of cities'
    )
    parser.add_argument(
        '-c', '--city',
        required=True,
        help='Anchor city to measure distances from'
    )
    parser.add_argument(
        '-r', '--radius',
        type=float,
        required=True,
        help='Maximum radius in miles to consider cities'
    )

    return parser.parse_args()

def validate_inputs(args: argparse.Namespace) -> None:
    """Validate input parameters."""
    if args.radius <= 0:
        raise ValueError("Radius must be greater than 0")

    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("Google Maps API key not found in environment variables")

def find_closest_city(
    cities: List[str],
    anchor_city: str,
    max_radius: float,
    gmaps: googlemaps.Client = None
) -> Tuple[str, float, Dict]:
    """Find the closest city by driving distance within specified radius."""
    try:
        if gmaps is None:
            gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

        # Geocode anchor city
        anchor_coords = geocode_city(gmaps, anchor_city)

        # Filter cities by linear distance first
        cities_in_radius: Dict[str, Tuple[float, float]] = {}

        print(f"\nCalculating linear distances from {anchor_city}...")
        for city in cities:
            if city == anchor_city:
                continue

            try:
                coords = geocode_city(gmaps, city)
                linear_distance = haversine_distance(anchor_coords, coords)

                print(f"{city}: {linear_distance:.2f} miles (linear)", end='')
                if linear_distance <= max_radius:
                    cities_in_radius[city] = coords
                    print(" - within radius")
                else:
                    print(" - excluded (outside radius)")
            except Exception as e:
                print(f"Warning: Could not process {city}: {str(e)}")
                continue

        if not cities_in_radius:
            raise ValueError(f"No cities found within {max_radius} miles radius")

        # Calculate driving distances for filtered cities
        print(f"\nCalculating driving distances for {len(cities_in_radius)} cities within radius...")
        closest_city = None
        min_distance = float('inf')

        for city in cities_in_radius:
            try:
                distance = get_driving_distance(gmaps, anchor_city, city)
                print(f"{city}: {distance:.2f} miles (driving)")

                if distance < min_distance:
                    min_distance = distance
                    closest_city = city
            except Exception as e:
                print(f"Warning: Could not calculate driving distance to {city}: {str(e)}")
                continue

        if closest_city is None:
            raise ValueError("Could not find any reachable cities by driving")

        return closest_city, min_distance, {"lat": anchor_coords[0], "lng": anchor_coords[1]}
    except Exception as e:
        raise Exception(f"Error finding closest city: {str(e)}")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/find', methods=['POST'])
def find():
    """Handle the form submission and find the closest city."""
    try:
        anchor_city = request.form['anchor_city']
        radius = float(request.form['radius'])
        cities_text = request.form['cities']

        # Create a temporary file to store the cities
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(cities_text)
            temp_file.flush()

        # Read cities from the temporary file
        cities = read_cities_file(temp_file.name)
        if not cities:
            raise ValueError("No cities found in input")

        # Find closest city
        closest_city, distance, start_location = find_closest_city(
            cities,
            anchor_city,
            radius
        )

        result = {
            'anchor_city': anchor_city,
            'closest_city': closest_city,
            'distance': distance,
            'start_location': start_location
        }

        return render_template('index.html', 
                             result=result,
                             google_maps_api_key=GOOGLE_MAPS_API_KEY)

    except Exception as e:
        return f"Error: {str(e)}", 400

def main() -> None:
    """Main function."""
    try:
        # Parse and validate arguments
        args = parse_arguments()

        if args is None:  # No command line arguments, run as web app
            app.run(host='0.0.0.0', port=5000, debug=True)
            return

        validate_inputs(args)

        # Read cities from file
        cities = read_cities_file(args.file)
        if not cities:
            raise ValueError("No cities found in input file")

        print(f"\nProcessing {len(cities)} unique cities...")
        print(f"Searching for closest city to {args.city} within {args.radius} miles radius...")

        # Find closest city
        closest_city, distance, _ = find_closest_city(
            cities,
            args.city,
            args.radius
        )

        print(f"\nResult:")
        print(f"Closest city: {closest_city}")
        print(f"Driving distance: {distance:.2f} miles")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()