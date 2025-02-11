import math
from typing import List, Tuple, Dict
import googlemaps
from config import EARTH_RADIUS_MILES

def read_cities_file(filename: str) -> List[str]:
    """Read cities from a text file and remove duplicates."""
    try:
        with open(filename, 'r') as f:
            # Read all non-empty lines and store in a set to remove duplicates
            cities = list({line.strip() for line in f if line.strip()})
            if not cities:
                raise ValueError("No valid cities found in the file")
            return cities
    except FileNotFoundError:
        raise FileNotFoundError(f"Cities file '{filename}' not found")
    except Exception as e:
        raise Exception(f"Error reading cities file: {str(e)}")

def geocode_city(gmaps_client: googlemaps.Client, city: str) -> Tuple[float, float]:
    """Geocode a city name to coordinates."""
    try:
        # Add more context to the geocoding request
        result = gmaps_client.geocode(f"{city}, United States")
        if not result:
            raise ValueError(f"No results found for city: {city}")

        location = result[0]['geometry']['location']
        return location['lat'], location['lng']
    except googlemaps.exceptions.ApiError as e:
        raise Exception(f"Google Maps API error for {city}: {str(e)}")
    except (KeyError, IndexError):
        raise ValueError(f"Invalid geocoding response format for city: {city}")
    except Exception as e:
        raise Exception(f"Error geocoding {city}: {str(e)}")

def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calculate the linear distance between two coordinates using haversine formula."""
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS_MILES * c

def get_driving_distance(
    gmaps_client: googlemaps.Client,
    origin: str,
    destination: str
) -> float:
    """Get driving distance between two cities using Google Maps Distance Matrix API."""
    try:
        # Add state context to make the search more accurate
        origin_query = f"{origin}, United States"
        dest_query = f"{destination}, United States"

        result = gmaps_client.distance_matrix(
            origins=[origin_query],
            destinations=[dest_query],
            mode="driving",
            units="imperial"
        )

        # Check the overall response status
        if result.get('status') != 'OK':
            raise ValueError(f"API Error: {result.get('status')} - Could not calculate distance")

        # Check if we have valid results
        if not result.get('rows') or not result['rows'][0].get('elements'):
            raise ValueError("Invalid response format from Distance Matrix API")

        element = result['rows'][0]['elements'][0]

        # Check the individual result status
        if element['status'] != 'OK':
            raise ValueError(f"Route Error: {element['status']} - No route found between {origin} and {destination}")

        # Convert meters to miles
        distance_miles = element['distance']['value'] * 0.000621371
        return distance_miles

    except googlemaps.exceptions.ApiError as e:
        raise Exception(f"Google Maps API error: {str(e)}")
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected response format: {str(e)}")
    except Exception as e:
        raise Exception(f"Error calculating driving distance: {str(e)}")