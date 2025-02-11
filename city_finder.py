#!/usr/bin/env python3

import argparse
import sys
import tempfile
import os
from typing import Dict, List, Tuple, Optional
import googlemaps
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_migrate import Migrate
from config import GOOGLE_MAPS_API_KEY
from utils import (
    read_cities_file,
    geocode_city,
    haversine_distance,
    get_driving_distance
)
from models import db, SearchHistory

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add SSL and connection pool settings
if app.config['SQLALCHEMY_DATABASE_URI']:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "sslmode": "require"
        }
    }

# Initialize the database and migrations
db.init_app(app)
migrate = Migrate(app, db)

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
            if city.lower() == anchor_city.lower():
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
    """Render the main page with search history."""
    search_history = SearchHistory.query.order_by(SearchHistory.created_at.desc()).limit(5).all()
    return render_template('index.html', 
                         search_history=search_history,
                         google_maps_api_key=GOOGLE_MAPS_API_KEY)

@app.route('/find', methods=['POST'])
def find():
    """Handle the form submission and find the closest city."""
    try:
        anchor_city = request.form['anchor_city'].strip()
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

        # Save search history to database
        search_history = SearchHistory(
            anchor_city=anchor_city.title(),
            closest_city=closest_city.title(),
            driving_distance=distance,
            radius=radius,
            searched_cities=','.join(cities)
        )
        db.session.add(search_history)
        db.session.commit()

        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'anchor_city': anchor_city.title(),
                'closest_city': closest_city.title(),
                'distance': distance,
                'start_location': start_location,
                'google_maps_api_key': GOOGLE_MAPS_API_KEY
            })

        # For regular form submission, return HTML
        result = {
            'anchor_city': anchor_city.title(),
            'closest_city': closest_city.title(),
            'distance': distance,
            'start_location': start_location
        }
        return render_template('index.html',
                            result=result,
                            google_maps_api_key=GOOGLE_MAPS_API_KEY,
                            search_history=SearchHistory.query.order_by(SearchHistory.created_at.desc()).limit(5).all())

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return str(e), 400
        return f"Error: {str(e)}", 400

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get search history as JSON."""
    history = SearchHistory.query.order_by(SearchHistory.created_at.desc()).limit(10).all()
    return jsonify([h.to_dict() for h in history])

def main() -> None:
    """Main function."""
    try:
        # Parse and validate arguments
        args = parse_arguments()

        if args is None:  # No command line arguments, run as web app
            with app.app_context():
                db.create_all()  # Create tables when running as web app
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