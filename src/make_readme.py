"""Regenerate README.md from the built data so its numbers always match the page.

    python src/make_readme.py [pages_url]
"""
import csv, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'intersections.csv'), encoding='utf-8')))
d = json.load(open(os.path.join(ROOT, 'data', 'network.json'), encoding='utf-8'))
M, S = d['metrics'], d['intsum']
by = {i['id']: i for i in d['ints']}
url_file = os.path.join(ROOT, 'docs', '.pages_url')
if len(sys.argv) > 1:
    open(url_file, 'w').write(sys.argv[1])
pages = open(url_file).read().strip() if os.path.exists(url_file) else None

lower = lambda t: t[0].lower() + t[1:]
tbl = ('| # | Intersection | Walk/bike crashes | Fatal or serious (all vehicles) | All crashes | Main problem in the crash reports | Lead fixes |\n'
       '|---|---|---|---|---|---|---|\n')
for r in rows:
    i = by[r['id']]
    vru = int(r['bike_crashes']) + int(r['ped_crashes'])
    tbl += (f"| {r['rank']} | {r['intersection']} | {vru} ({r['bike_crashes']} bike, {r['ped_crashes']} walking) | "
            f"{r['fatal_or_serious_all_modes']} | {r['all_crashes']} | {i['issues'][0]} | "
            f"{i['fixes'][0]['fix']}; {lower(i['fixes'][1]['fix'])} |\n")

st = {k: [x for x in d['corridors'] + d['greenways'] if x['status'] == k] for k in ('endorse', 'modify', 'new')}
mi = lambda k: round(sum(x['miles'] for x in st[k]), 1)
total = round(M['miles']['protected'] + M['miles']['sidepath'] + M['miles']['connector'] + M['miles']['greenway'], 1)
right = sum(i['st']['vru_right'] for i in d['ints'])
live = f'**Live page:** {pages}\n\n' if pages else 'Open [`docs/index.html`](docs/index.html) in a browser to view the page.\n\n'

readme = f"""# Decatur Connects

A citizen proposal for a connected, protected bike network in Decatur, Georgia, built from the
city's own crash records and adopted plans.

{live}The page has an interactive map, a comparison with what the city and GDOT already plan, a crash
analysis, and a problem-and-fix write-up for each of {S['n']} priority intersections, with lane-by-lane
plans of each one as striped today and as proposed.

## What it proposes

- **{total} miles** of new protected bike lanes, shared-use paths and neighborhood greenways in
  {len(d['corridors'])} corridors and {len(d['greenways'])} greenways.
- All **{M['public_schools']} public schools** within a quarter mile of a low-stress route ({M['pub_before']} today).
- A new **West Side Connector**: a north-south route on Adair St and Mead Rd that uses the rail
  crossing the city approved in concept in 2019.
- Lanes are removed only where traffic volumes fit a 4-to-3 conversion. Scott Blvd (about 40,000
  vehicles a day) keeps every lane and gets a path behind the curb.

Most of the network is already in a city, PATH Foundation or GDOT plan:

| | Pieces | Miles |
|---|---|---|
| Already proposed; endorsed as is | {len(st['endorse'])} | {mi('endorse')} |
| Builds on a city plan; design, extent or timing changed | {len(st['modify'])} | {mi('modify')} |
| New in this proposal | {len(st['new'])} | {mi('new')} |

## What the crash records show

Decatur recorded {S['total_all']:,} crashes from 2019 to 2023. {S['vru_all']} involved someone walking or biking
({M['bike']['total']} bike, {M['ped']['total']} pedestrian), and {S['vru_fsi_all']} of those were fatal or serious.

- {S['vru']} of the {S['vru_all']} walking and biking crashes, and {S['vru_fsi']} of the {S['vru_fsi_all']} fatal or serious ones,
  happened within {S['radius_ft']} ft of the {S['n']} intersections below.
- At those intersections, {S['vru_left']} of {S['vru']} involved a driver turning left.
- {M['bike']['on']} of {M['bike']['total']} bike crashes citywide were on a street this proposal would rebuild.

## The intersections: problem and fix

Each row is a crash cluster on or beside the proposed network. The page gives the full list of
issues and fixes for each, a crash map, and the measured effect of each treatment where a federal
figure exists. The same data is in [`data/intersections.csv`](data/intersections.csv).

{tbl}
Three patterns repeat, and each has a matching treatment:

| Pattern | Walk/bike crashes at these sites | Treatment |
|---|---|---|
| Driver turning left into a crosswalk or an oncoming rider | {S['vru_left']} of {S['vru']} | Protected-only left-turn arrows, leading pedestrian intervals, hardened centerlines |
| Driver turning right across a crosswalk, trail or bike lane | {right} of {S['vru']} | No right turn on red, raised crossings, protected corners |
| After dark | {S['vru_dark']} of {S['vru']} | Lighting, high-visibility crosswalks, tall reflective posts |

## Intersection plans

Each intersection card on the page has two plan views drawn to scale: **Today** and **Proposed**.

- Streets follow their real OpenStreetMap centerlines, so angles, curves and offsets match the ground.
- Each street segment has a cross-section (lanes, turn lanes, medians, parking, bike lanes, buffers,
  sidewalks) written in [`src/layouts.py`](src/layouts.py). The existing layouts were checked against
  Esri and Google aerial imagery and Google Street View in November 2026, and the drawings were
  overlaid on the aerial photos to check alignment.
- Proposed protected intersections bend each bike lane out about 15 ft before the corner, leaving
  concrete corner islands between riders and turning cars, with the bike crossing just inside the
  crosswalk.
- Numbered markers on the proposed plan match the numbered fixes in the card. Signal changes
  (turn arrows, pedestrian head starts, no turn on red) are marked at the approach they apply to.
- Turn arrows are drawn only where imagery or OSM tags confirm them. Where a lane's arrow could not
  be read, none is drawn.

## Method

1. **Crash data.** All {S['total_all']:,} crash records behind the city's 2025 Safe Streets Safety Action Plan,
   pulled from the city's public ArcGIS feature service (`src/fetch_data.py`).
2. **Street network.** OpenStreetMap streets loaded into a `networkx` graph. Corridors are snapped
   to named streets. Greenways are routed with a least-stress cost: arterials cost far more per
   foot than residential streets.
3. **Intersections.** Walking and biking crashes were clustered by location to rank sites. Every
   crash within {S['radius_ft']} ft of a site is counted once, at the nearest site. The "issues" text
   summarises the police narratives; counts come from the coded fields.
4. **Plan comparison.** Each corridor was checked against the 2016 PATH Connectivity Plan, the
   2025 Safety Action Plan, 2026 city projects and GDOT's programmed work.

## Reproduce

```
pip install -r requirements.txt
python src/fetch_data.py        # optional: re-download the crash records
python src/build_network.py     # writes data/*.csv, data/network.json and docs/index.html
python src/make_readme.py       # refreshes the numbers in this file
```

| Path | What it is |
|---|---|
| `docs/index.html` | The proposal page (self-contained) |
| `src/build_network.py` | Network routing, crash analysis, page build |
| `src/intersections.py` | Intersection definitions, issues, fixes and evidence |
| `src/layouts.py` | Lane-by-lane layouts of each intersection, today and proposed |
| `src/diagrams.py` | Draws the plan views from OSM geometry and the layouts |
| `src/fetch_data.py` | Data download |
| `data/crashes_2019_2023.csv` | All crashes, coded fields only (no narratives) |
| `data/bike_ped_crashes_2019_2023.csv` | The {S['vru_all']} walking and biking crashes |
| `data/intersections.csv` | Crash profile and fixes for each priority intersection |
| `data/snapshot/` | OpenStreetMap streets (citywide and around each intersection), city High Injury Network, city limits |

## Limits

- This is a planning-level proposal, not an engineering design. Every corridor needs survey and
  traffic analysis, and GDOT review on state routes.
- Only the Clairemont Ave and Commerce Dr traffic volumes are official GDOT counts. The others
  are estimates from a field in the crash records.
- Five years of crashes at one intersection is a small sample. The crash-reduction percentages
  are federal averages for each treatment, not predictions for these sites.
- Police reports undercount bike and pedestrian crashes, and the coded "maneuver" field does not
  always match the narrative.
- Greenway routes were chosen by an algorithm and need to be walked with neighbors and schools.

## Sources

- [Decatur Safe Streets Safety Action Plan](https://www.decaturga.com/publicworks/page/decatur-safe-streets-safety-action-plan) (2025) and its
  [crash data service](https://services.arcgis.com/36QtML6Mf01B1N0W/arcgis/rest/services/High_Injury_Network_Data/FeatureServer)
- [Decatur PATH Connectivity and Implementation Plan](https://www.decaturga.com/planning/page/path-connectivity-implementation-plan-2016) (2016)
- City of Decatur project pages for Church St and Clairemont Ave, W Ponce de Leon Ave, W Howard Ave, E Lake Dr and S McDonough St
- [FHWA Proven Safety Countermeasures](https://highways.dot.gov/safety/proven-safety-countermeasures); road diet and bicycle lane figures from FHWA-HRT-10-053 and the FHWA bicycle lanes fact sheet
- FHWA Separated Bike Lane Planning and Design Guide; NACTO Urban Bikeway Design Guide
- Street data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL
"""
open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8').write(readme)
print('wrote README.md')
