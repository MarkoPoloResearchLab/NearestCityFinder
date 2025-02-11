import os

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

# Constants
EARTH_RADIUS_MILES = 3959  # Earth's radius in miles
MAX_CITIES_PER_REQUEST = 25  # Google Maps API limit for distance matrix
