# Decatur Connects

A citizen proposal for a connected, protected bike network in Decatur, Georgia, built from the
city's own crash records and adopted plans.

**Live page:** https://klovelace.github.io/decatur-connects/

The page has an interactive map, a comparison with what the city and GDOT already plan, a crash
analysis, and a problem-and-fix write-up for each of 12 priority intersections.

## What it proposes

- **14.5 miles** of new protected bike lanes, shared-use paths and neighborhood greenways in
  12 corridors and 6 greenways.
- All **9 public schools** within a quarter mile of a low-stress route (5 today).
- A new **West Side Connector**: a north-south route on Adair St and Mead Rd that uses the rail
  crossing the city approved in concept in 2019.
- Lanes are removed only where traffic volumes fit a 4-to-3 conversion. Scott Blvd (about 40,000
  vehicles a day) keeps every lane and gets a path behind the curb.

Most of the network is already in a city, PATH Foundation or GDOT plan:

| | Pieces | Miles |
|---|---|---|
| Already proposed; endorsed as is | 7 | 5.3 |
| Builds on a city plan; design, extent or timing changed | 6 | 4.8 |
| New in this proposal | 5 | 5.1 |

## What the crash records show

Decatur recorded 3,451 crashes from 2019 to 2023. 93 involved someone walking or biking
(38 bike, 55 pedestrian), and 19 of those were fatal or serious.

- 47 of the 93 walking and biking crashes, and 13 of the 19 fatal or serious ones,
  happened within 250 ft of the 12 intersections below.
- At those intersections, 19 of 47 involved a driver turning left.
- 22 of 38 bike crashes citywide were on a street this proposal would rebuild.

## The intersections: problem and fix

Each row is a crash cluster on or beside the proposed network. The page gives the full list of
issues and fixes for each, a crash map, and the measured effect of each treatment where a federal
figure exists. The same data is in [`data/intersections.csv`](data/intersections.csv).

| # | Intersection | Walk/bike crashes | Fatal or serious (all vehicles) | All crashes | Main problem in the crash reports | Lead fixes |
|---|---|---|---|---|---|---|
| 1 | E College Ave / S Candler St / E Trinity Pl / E Howard Ave | 9 (3 bike, 6 walking) | 3 | 257 | Six walking and biking crashes involved a driver turning left who did not yield to someone in the crosswalk or to an oncoming rider. | Protected-only left-turn arrows on E College Ave and S Candler St; leading pedestrian interval and no right turn on red |
| 2 | Commerce Dr / W Trinity Pl / Swanton Way | 8 (2 bike, 6 walking) | 1 | 62 | At least four pedestrians were hit in the crosswalk by drivers turning left from Swanton Way or W Trinity Pl. Several had the walk signal. | Protected-only left turns from Swanton Way and W Trinity Pl, separated in time from the walk signal; leading pedestrian interval at both signals |
| 3 | W Ponce de Leon Ave / W Trinity Pl / Adair St | 5 (2 bike, 3 walking) | 2 | 11 | A rider in the bike lane was seriously injured by a driver changing lanes where the lane drops. | Carry the protected bike lane through the intersection; end the merge; replace low domes with tall reflective posts or a continuous curb |
| 4 | E College Ave / Commerce Dr | 5 (3 bike, 2 walking) | 3 | 134 | A pedestrian standing on the sidewalk was killed in 2023 when a left-turning driver lost control. | Protected intersection with corner islands as part of the GDOT road diet; protected-only left-turn arrows |
| 5 | N Candler St / Commerce Dr | 4 (1 bike, 3 walking) | 4 | 34 | Four serious-injury crashes in five years, the most of any site on this list. | Road diet on Commerce Dr: one through lane each way plus a turn lane; pedestrian refuge island on Commerce Dr |
| 6 | Atlanta Ave / W Howard Ave / W College Ave | 4 (3 bike, 1 walking) | 0 | 41 | Two riders on the trail crossing were hit by right-turning drivers. One driver was rolling forward on a red light while looking left. | Build the 2019 concept: new Adair St crossing with signals at W College Ave and Olympic Pl; no right turn on red and a raised trail crossing |
| 7 | S McDonough St / College Ave / Howard Ave | 3 (3 bike, 0 walking) | 1 | 101 | A rider crossing S McDonough St on College Ave suffered a head injury when a driver entered the intersection. | Protected intersection with a bike signal phase; separated bike lanes on College Ave (C5, C6) |
| 8 | Church St / E Trinity Pl | 3 (0 bike, 3 walking) | 2 | 29 | All three pedestrian crashes involved a driver turning left into the crosswalk. | Protected-only left-turn arrows, with the walk signal held during the arrow; leading pedestrian interval |
| 9 | Oakview Rd / Mead Rd | 2 (1 bike, 1 walking) | 1 | 6 | A pedestrian in the marked crosswalk was seriously injured by a driver who did not yield. | Raised crosswalk with a flashing beacon; curb extensions that shorten the crossing and open sight lines |
| 10 | Church St / Glenlake Commons Dr | 2 (2 bike, 0 walking) | 0 | 7 | Two riders on the cycle track were hit in 2023 by drivers turning right out of Glenlake Commons Dr. | Raised crossing so the bikeway stays level and drivers climb a ramp; stop bar set back behind the bikeway, with green conflict markings and a "look both ways for bikes" sign |
| 11 | Scott Blvd / Clairemont Ave | 1 (0 bike, 1 walking) | 1 | 150 | A pedestrian in the crosswalk was killed in 2022. | Roundabout or protected-only left turns, decided in the Scott Blvd RAISE study; upgrade lighting on all four corners |
| 12 | Clairemont Ave / Commerce Dr | 1 (1 bike, 0 walking) | 0 | 130 | A rider in the marked bike lane was hit by a driver turning right across the lane. | Protected corners with a bike signal or set-back crossing; road diets on Clairemont Ave and Commerce Dr east (C1, C3) |

Three patterns repeat, and each has a matching treatment:

| Pattern | Walk/bike crashes at these sites | Treatment |
|---|---|---|
| Driver turning left into a crosswalk or an oncoming rider | 19 of 47 | Protected-only left-turn arrows, leading pedestrian intervals, hardened centerlines |
| Driver turning right across a crosswalk, trail or bike lane | 9 of 47 | No right turn on red, raised crossings, protected corners |
| After dark | 10 of 47 | Lighting, high-visibility crosswalks, tall reflective posts |

## Method

1. **Crash data.** All 3,451 crash records behind the city's 2025 Safe Streets Safety Action Plan,
   pulled from the city's public ArcGIS feature service (`src/fetch_data.py`).
2. **Street network.** OpenStreetMap streets loaded into a `networkx` graph. Corridors are snapped
   to named streets. Greenways are routed with a least-stress cost: arterials cost far more per
   foot than residential streets.
3. **Intersections.** Walking and biking crashes were clustered by location to rank sites. Every
   crash within 250 ft of a site is counted once, at the nearest site. The "issues" text
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
| `src/fetch_data.py` | Data download |
| `data/crashes_2019_2023.csv` | All crashes, coded fields only (no narratives) |
| `data/bike_ped_crashes_2019_2023.csv` | The 93 walking and biking crashes |
| `data/intersections.csv` | Crash profile and fixes for each priority intersection |
| `data/snapshot/` | OpenStreetMap streets, city High Injury Network, city limits |

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
