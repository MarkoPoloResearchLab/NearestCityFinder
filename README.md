# Nearest City Finder

A command-line tool that finds the closest city by driving distance within a specified radius using the Google Maps API.

## Features

- Finds the nearest city from a list of cities based on actual driving distance
- Filters cities by linear distance first to optimize API usage
- Supports custom radius limits
- Deduplicates city entries automatically
- Shows both linear and driving distances for better comparison

## Prerequisites

- Python 3.x
- Google Maps API key with the following APIs enabled:
  - Geocoding API
  - Distance Matrix API

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MarkoPoloResearchLab/NearestCityFinder.git
cd NearestCityFinder
```

2. Install dependencies:
```bash
pip install googlemaps
```

3. Set up your Google Maps API key:
```bash
export GOOGLE_MAPS_API_KEY='your_api_key_here'
```

## Usage

```bash
python city_finder.py -f cities.txt -c "San Francisco" -r 300
```

Arguments:
- `-f, --file`: Path to text file containing list of cities (one city per line)
- `-c, --city`: Anchor city to measure distances from
- `-r, --radius`: Maximum radius in miles to consider cities

## Example Output

```
Processing 44 unique cities...
Searching for closest city to San Ramon within 300.0 miles radius...

Calculating linear distances from San Ramon...
SAUSALITO: 29.73 miles (linear) - within radius
PALO ALTO: 24.57 miles (linear) - within radius
SUNNYVALE: 27.70 miles (linear) - within radius
SANTA CLARA: 28.35 miles (linear) - within radius
RENO: 167.97 miles (linear) - within radius
...

Calculating driving distances for 8 cities within radius...
SAUSALITO: 51.34 miles (driving)
PALO ALTO: 42.30 miles (driving)
SUNNYVALE: 36.84 miles (driving)
SANTA CLARA: 36.70 miles (driving)
...

Result:
Closest city: SANTA CLARA
Driving distance: 36.70 miles
```

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
