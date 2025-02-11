git clone https://github.com/MarkoPoloResearchLab/NearestCityFinder.git
cd NearestCityFinder
```

2. Install dependencies:
```bash
pip install googlemaps flask flask-sqlalchemy flask-migrate psycopg2-binary
```

3. Set up environment variables:
```bash
export GOOGLE_MAPS_API_KEY='your_api_key_here'
export DATABASE_URL='your_postgres_database_url'
```

## Usage

### Command Line
```bash
python city_finder.py -f cities.txt -c "San Francisco" -r 300
```

Arguments:
- `-f, --file`: Path to text file containing list of cities (one city per line)
- `-c, --city`: Anchor city to measure distances from
- `-r, --radius`: Maximum radius in miles to consider cities

### Web Application
```bash
python city_finder.py
```
Then visit http://localhost:5000 in your web browser.

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