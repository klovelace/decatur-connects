"""Download the source data for the Decatur Connects analysis.

    python src/fetch_data.py            # crash records only (rebuilds data/crashes_2019_2023.csv)
    python src/fetch_data.py --all      # also refresh the OSM / HIN / city-limit snapshots

Sources
  * City of Decatur "High Injury Network Data" feature service (the data behind the 2025
    Safe Streets Safety Action Plan). Layer 2 = crashes 2019-2023, layer 3 = HIN/HRN segments.
  * City of Decatur city-limits feature service.
  * OpenStreetMap via the Overpass API (street geometry and existing bike facilities).

The raw crash download includes police narratives. Those stay in data/raw/ (git-ignored);
only a slim table without narratives is written to data/crashes_2019_2023.csv.
"""
import csv, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
SNAP = os.path.join(ROOT, 'data', 'snapshot')
UA = {'User-Agent': 'decatur-connects-analysis/1.0'}

HIN = 'https://services.arcgis.com/36QtML6Mf01B1N0W/arcgis/rest/services/High_Injury_Network_Data/FeatureServer'
CITY = 'https://services.arcgis.com/36QtML6Mf01B1N0W/arcgis/rest/services/Decatur_City_Limits/FeatureServer/4'
OVERPASS = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter']
BBOX = '33.752,-84.322,33.800,-84.268'
OSM_QUERY = f'''[out:json][timeout:120];
way["highway"~"^(trunk|trunk_link|primary|secondary|tertiary|residential|unclassified|cycleway|path|living_street|primary_link|secondary_link|tertiary_link)$"]({BBOX});
out body geom;'''

# Columns kept in the published crash table (no narratives, no names).
SLIM = ['collision_id', 'col_date', 'col_year', 'hour', 'crash_mode', 'crash_severity', 'crash_severity_long',
        'primary_road', 'intersecting_road', 'location_at_impact', 'manner_collision', 'veh1_maneuver',
        'left_vs_straight', 'speedlimit', 'num_lanes', 'owned_by', 'signalized_intersection',
        'lighting_condition', 'speed_related', 'hit_and_run', 'aadt']


def get(url, data=None, timeout=180):
    req = urllib.request.Request(url, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_layer(url, page=2000):
    feats, off = [], 0
    while True:
        q = urllib.parse.urlencode({'where': '1=1', 'outFields': '*', 'outSR': 4326, 'resultOffset': off,
                                    'resultRecordCount': page, 'f': 'geojson'})
        got = json.loads(get(f'{url}/query?{q}'))['features']
        feats += got
        if len(got) < page:
            return feats
        off += page


def load_raw_crashes():
    feats = []
    for name in sorted(os.listdir(RAW)):
        if name.startswith('crashes') and name.endswith('.geojson'):
            feats += json.load(open(os.path.join(RAW, name), encoding='utf-8'))['features']
    return feats


def write_slim(feats):
    path = os.path.join(ROOT, 'data', 'crashes_2019_2023.csv')
    n = 0
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(SLIM + ['lat', 'lon'])
        for f in sorted(feats, key=lambda f: str(f['properties']['collision_id'])):
            if not f.get('geometry'):
                continue
            lon, lat = f['geometry']['coordinates'][:2]
            p = f['properties']
            w.writerow([p.get(c) for c in SLIM] + [round(lat, 6), round(lon, 6)])
            n += 1
    print(f'wrote {n} crashes -> {os.path.relpath(path, ROOT)}')


def main():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(SNAP, exist_ok=True)
    if '--offline' not in sys.argv:
        feats = fetch_layer(f'{HIN}/2')
        json.dump({'type': 'FeatureCollection', 'features': feats},
                  open(os.path.join(RAW, 'crashes_all.geojson'), 'w', encoding='utf-8'))
        for old in ('crashes_0.geojson', 'crashes_2000.geojson'):
            if os.path.exists(os.path.join(RAW, old)):
                os.remove(os.path.join(RAW, old))
        print(f'downloaded {len(feats)} crash records')
    write_slim(load_raw_crashes())

    if '--all' in sys.argv:
        json.dump({'type': 'FeatureCollection', 'features': fetch_layer(f'{HIN}/3')},
                  open(os.path.join(SNAP, 'hin_hrn.geojson'), 'w', encoding='utf-8'))
        json.dump({'type': 'FeatureCollection', 'features': fetch_layer(CITY)},
                  open(os.path.join(SNAP, 'city_limits.geojson'), 'w', encoding='utf-8'))
        body = urllib.parse.urlencode({'data': OSM_QUERY}).encode()
        for attempt, url in enumerate(OVERPASS * 2):
            try:
                raw = get(url, body)
                json.loads(raw)['elements']
                open(os.path.join(SNAP, 'osm_ways.json'), 'wb').write(raw)
                print('refreshed OSM snapshot from', url)
                break
            except Exception as e:  # Overpass is often busy; try the next mirror
                print('overpass failed:', url, e)
                time.sleep(10 * (attempt + 1))
        else:
            sys.exit('could not refresh OSM snapshot; existing snapshot left in place')


if __name__ == '__main__':
    main()
