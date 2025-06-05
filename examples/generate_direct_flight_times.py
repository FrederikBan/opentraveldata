# Script to compute estimated direct flight times between airports
# using OPTD datasets.

import csv
import json
import math
from collections import defaultdict

POR_FILE = 'opentraveldata/optd_por_public.csv'
ROUTES_FILE = 'opentraveldata/optd_airline_por.csv'
OUTPUT_JSON = 'direct_flight_times.json'
AVG_SPEED_KMH = 850.0  # assume average cruise speed


def load_coordinates(filename):
    coords = {}
    names = {}
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='^')
        for row in reader:
            iata = row.get('iata_code', '').strip()
            if not iata:
                continue
            try:
                lat = float(row['latitude'])
                lon = float(row['longitude'])
            except (ValueError, KeyError):
                continue
            coords[iata] = (lat, lon)
            name = row.get('name') or row.get('asciiname') or iata
            names[iata] = name
    return coords, names


def load_routes(filename):
    routes = defaultdict(set)
    with open(filename, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='^')
        for row in reader:
            o = row.get('apt_org', '').strip()
            d = row.get('apt_dst', '').strip()
            if o and d:
                routes[o].add(d)
    return routes


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0  # radius of Earth in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return r * c


def build_flight_time_table(coords, routes):
    table = {}
    for origin, dests in routes.items():
        if origin not in coords:
            continue
        table[origin] = {}
        lat1, lon1 = coords[origin]
        for dest in dests:
            if dest not in coords:
                continue
            lat2, lon2 = coords[dest]
            dist = haversine(lat1, lon1, lat2, lon2)
            time_minutes = (dist / AVG_SPEED_KMH) * 60.0
            table[origin][dest] = round(time_minutes, 2)
        if not table[origin]:
            table.pop(origin)
    return table


def main():
    coords, names = load_coordinates(POR_FILE)
    routes = load_routes(ROUTES_FILE)
    table = build_flight_time_table(coords, routes)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(table, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
