"""Build the Decatur Connects proposal page from the crash table and street snapshots.

    python src/build_network.py

Inputs
  data/crashes_2019_2023.csv        City of Decatur crash records (see fetch_data.py)
  data/snapshot/osm_ways.json       OpenStreetMap streets and bike facilities
  data/snapshot/hin_hrn.geojson     City High Injury / High Risk Network segments
  data/snapshot/city_limits.geojson City limits
  src/intersections.py              Priority intersections, issues and fixes
  src/template.html                 Page template
Outputs
  data/network.json                 Projected map geometry, corridors, crashes, metrics
  data/intersections.csv            Crash profile of each priority intersection
  data/bike_ped_crashes_2019_2023.csv
  docs/index.html                   Standalone page (GitHub Pages)
  decatur-connects.html             Same page as a fragment (git-ignored)
"""
import csv, json, math, collections, sys, os
import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from intersections import INTERSECTIONS, EVIDENCE, RADIUS_M
import diagrams
from layouts import LAYOUTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
SNAP = os.path.join(DATA, 'snapshot')
ways = json.load(open(os.path.join(SNAP, 'osm_ways.json'), encoding='utf-8'))['elements']
hrn = json.load(open(os.path.join(SNAP, 'hin_hrn.geojson'), encoding='utf-8'))['features']
city = json.load(open(os.path.join(SNAP, 'city_limits.geojson'), encoding='utf-8'))['features'][0]['geometry']

INT_COLS = ('col_year', 'left_vs_straight', 'signalized_intersection', 'speed_related', 'hit_and_run')
crashes = []  # same shape as GeoJSON features so the rest of the script reads either
with open(os.path.join(DATA, 'crashes_2019_2023.csv'), encoding='utf-8', newline='') as fh:
    for row in csv.DictReader(fh):
        for k in INT_COLS:
            row[k] = int(row[k]) if row[k] not in ('', None) else 0
        crashes.append({'properties': row, 'geometry': {'coordinates': [float(row['lon']), float(row['lat'])]}})

LAT0 = 33.7745
COS = math.cos(math.radians(LAT0))
M_PER_DEG = 111320.0

def hav(a, b):
    (la1, lo1), (la2, lo2) = a, b
    dx = (lo2 - lo1) * COS * M_PER_DEG
    dy = (la2 - la1) * M_PER_DEG
    return math.hypot(dx, dy)

# ---------------- projection to SVG units ----------------
ring = city['coordinates'][0]
lons = [p[0] for p in ring]; lats = [p[1] for p in ring]
PAD = 0.006
LON_MIN, LON_MAX = min(lons) - PAD, max(lons) + PAD
LAT_MIN, LAT_MAX = min(lats) - PAD, max(lats) + PAD
W = 1000.0
SCALE = W / ((LON_MAX - LON_MIN) * COS)
H = (LAT_MAX - LAT_MIN) * SCALE

def P(lat, lon):
    return (round((lon - LON_MIN) * COS * SCALE, 1), round((LAT_MAX - lat) * SCALE, 1))

def inview(lat, lon, m=0.003):
    return LON_MIN - m <= lon <= LON_MAX + m and LAT_MIN - m <= lat <= LAT_MAX + m

def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i]
        d = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / L
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]

def path_d(lines, eps=0.6):
    out = []
    for ln in lines:
        pts = rdp([P(la, lo) for la, lo in ln], eps)
        if len(pts) < 2:
            continue
        out.append('M' + ' '.join(f'{x:g},{y:g}' for x, y in pts))
    return ''.join(out)

# ---------------- graph ----------------
G = nx.Graph()
coord = {}
CLASS_W = {'trunk': 60.0, 'trunk_link': 60.0, 'cycleway': 0.55, 'path': 0.7, 'living_street': 0.9, 'residential': 1.0, 'unclassified': 1.2,
           'tertiary': 4.0, 'tertiary_link': 4.0, 'secondary': 25.0, 'secondary_link': 25.0,
           'primary': 40.0, 'primary_link': 40.0}
for w in ways:
    g = w.get('geometry'); ns = w.get('nodes')
    if not g or not ns:
        continue
    t = w['tags']
    for nid, pt in zip(ns, g):
        coord[nid] = (pt['lat'], pt['lon'])
    for a, b in zip(ns, ns[1:]):
        L = hav(coord[a], coord[b])
        G.add_edge(a, b, length=L, name=t.get('name', ''), hw=t.get('highway'), wid=w['id'])

MAINCC = max(nx.connected_components(G), key=len)

def norm(n):
    return (n or '').lower().replace(' northeast', '').strip()

def nodes_on(name):
    s = set()
    global MAINCC
    for a, b, d in G.edges(data=True):
        if norm(d['name']) == norm(name) and a in MAINCC:
            s.add(a); s.add(b)
    return s

def X(n1, n2):
    """Node at the intersection of two named streets (closest pair if no shared node)."""
    A, B = nodes_on(n1), nodes_on(n2)
    if not A or not B:
        raise SystemExit(f'missing street {n1 if not A else n2}')
    common = A & B
    if common:
        return sorted(common)[0]
    best = min(((hav(coord[a], coord[b]), a) for a in A for b in B), key=lambda x: x[0])
    if best[0] > 120:
        print(f'WARN {n1} x {n2} nearest {best[0]:.0f} m', file=sys.stderr)
    return best[1]

def near(lat, lon, names=None):
    cands = coord.keys() if names is None else set().union(*[nodes_on(n) for n in names])
    cands = [c for c in cands if c in MAINCC]
    return min(cands, key=lambda c: hav(coord[c], (lat, lon)))

LOWNODES = {n for a, b, d in G.edges(data=True) if d['hw'] in ('residential', 'unclassified', 'living_street', 'cycleway') for n in (a, b)} & MAINCC
def near_low(lat, lon):
    return min(LOWNODES, key=lambda c: hav(coord[c], (lat, lon)))

def route(wps, prefer=None, mode='corridor'):
    pref = {norm(p) for p in (prefer or [])}
    def wt(a, b, d):
        if mode == 'corridor':
            f = 1.0 if norm(d['name']) in pref else 40.0
        else:
            f = 0.6 if frozenset((a, b)) in CORR_EDGES else CLASS_W.get(d['hw'], 3.0)
        return d['length'] * f
    seq = []
    for s, t in zip(wps, wps[1:]):
        p = nx.shortest_path(G, s, t, weight=wt)
        seq += p if not seq else p[1:]
    return seq

def seq_lines(seq):
    return [[coord[n] for n in seq]]

def seq_len_m(seq):
    return sum(hav(coord[a], coord[b]) for a, b in zip(seq, seq[1:]))

def seq_streets(seq):
    out = []
    for a, b in zip(seq, seq[1:]):
        n = G[a][b]['name'] or ('trail' if G[a][b]['hw'] in ('cycleway', 'path') else 'unnamed')
        if not out or out[-1][0] != n:
            out.append([n, 0.0])
        out[-1][1] += hav(coord[a], coord[b])
    return [n for n, L in out if L > 60]

# ---------------- proposals ----------------
CORR = [
 dict(id='C1', name='Clairemont Avenue', ext='Scott Blvd to Commerce Dr', streets=['Clairemont Avenue'],
      wps=[('Clairemont Avenue', 'Scott Boulevard'), ('Clairemont Avenue', 'Commerce Drive')],
      type='protected', phase=1, owner='GDOT (SR 155)', aadt='19,300 (GDOT 2023)',
      today='4 travel lanes, no bike facility, 35 mph',
      proposal='Road diet to 2 lanes + center turn lane. Year 1: 5-ft bike lanes with 2-ft buffer and flex posts in existing pavement (the Safety Action Plan\'s near-term option). Later: curb-separated one-way cycle tracks.',
      impact='Moderate', impactNote='19,300 vehicles/day is within the FHWA range where 4-to-3 conversions keep similar capacity, because the turn lane removes left-turn blockages. Needs a GDOT traffic operations study.',
      serves='Clairemont ES, Westchester ES (via Scott Blvd), downtown, Church St cycle track'),
 dict(id='C2', name='Church Street (downtown)', ext='Commerce Dr to E Ponce de Leon Ave', streets=['Church Street'],
      wps=[('Church Street', 'Commerce Drive'), ('Church Street', 'East Ponce de Leon Avenue')],
      type='protected', phase=1, owner='City', aadt='~18,500 (crash-layer estimate)',
      today='5 lanes (2 each way + turn lane), bike lanes end at Commerce',
      proposal='Back the city\'s 2026 quick-build Scenario 2: one lane each way, parking-protected bike lanes, barriers where parking is not possible, raised mid-block crossing.',
      impact='Low', impactNote='The block is short, with signals at both ends. Scenario 2 adds 9-11 parking spaces. Short blocks downtown are limited by the signals, not the number of lanes.',
      serves='Decatur Square, MARTA, library, Church St cycle track to Suburban Plaza'),
 dict(id='C3', name='Commerce Drive (east)', ext='Clairemont Ave to E College Ave', streets=['Commerce Drive'],
      wps=[('Commerce Drive', 'Clairemont Avenue'), ('Commerce Drive', 'East College Avenue')],
      type='protected', phase=2, owner='GDOT (SR 155)', aadt='12,500-13,000 (GDOT 2023)',
      today='4 lanes, measured speeds 36-40 mph, bike lanes end at Church St',
      proposal='Road diet with one-way protected bike lanes. Protected intersection at N Candler St, where a serious bike crash happened in 2022. Add speed management on the curves.',
      impact='Low', impactNote='12,500-13,000 vehicles/day is well under road-diet thresholds. Speeds of 36-40 mph, not capacity, are the problem here.',
      serves='Recreation Center, Talley St Upper ES, Glennwood ES, E College Ave'),
 dict(id='C4', name='S McDonough St - Oakview Rd spine', ext='W College Ave to Oakhurst Village', streets=['South McDonough Street', 'Oakview Road'],
      wps=[('South McDonough Street', 'West College Avenue'), ('South McDonough Street', 'Oakview Road'), ('Oakview Road', 'East Lake Drive')],
      type='protected', phase=2, owner='City', aadt='2,500-3,300 (crash-layer estimate)',
      today='2 lanes, traffic calming at College Heights, no bike facility',
      proposal='Build the Oakview / S McDonough PATH project as a two-way protected bikeway, with on-street parking kept on the opposite side. Include a protected crossing at the railroad and W College Ave.',
      impact='None', impactNote='Volumes are low, so this needs no lane reduction. The space comes from lane narrowing and putting parking on one side.',
      serves='Decatur HS, Beacon Hill MS, College Heights ECLC, Oakhurst ES, Oakhurst Village, McKoy Park'),
 dict(id='C5', name='West College Avenue', ext='East Lake MARTA to S McDonough St', streets=['West College Avenue'],
      wps=[('West College Avenue', 'East Lake Drive'), ('West College Avenue', 'South McDonough Street')],
      type='protected', phase=1, owner='GDOT (SR 10)', aadt='~15,000 (crash-layer estimate)',
      today='Wide lanes, painted bike lanes on parts',
      proposal='Lane diet (10-11 ft lanes) to free space for curb-separated or post-protected bike lanes, as the Safety Action Plan recommends. Upgrade Atlanta Ave and S McDonough St to protected intersections.',
      impact='Low', impactNote='Lanes get narrower but none are removed.',
      serves='Beacon Hill MS, East Lake MARTA, downtown'),
 dict(id='C6', name='East College Avenue', ext='S McDonough St to city limit (Avondale)', streets=['East College Avenue'],
      wps=[('East College Avenue', 'South McDonough Street'), ('East College Avenue', 'Sams Crossing')],
      type='protected', phase=2, owner='GDOT (SR 10)', aadt='~28,000 (crash-layer estimate)',
      today='4-5 lanes, 35 mph, most bike crashes of any Decatur street (6)',
      proposal='Back GDOT PI 0018335 (road diet + protected bike lane from the east city limit to S Candler St) and extend it west to S McDonough St. Protected intersection at Commerce Dr, which had 3 bike crashes.',
      impact='Study', impactNote='At ~28,000 vehicles/day a lane reduction needs GDOT corridor modeling. GDOT has already programmed it on the eastern segment.',
      serves='Agnes Scott College, Winnona Park ES, Talley St Upper ES, Avondale MARTA'),
 dict(id='C7', name='West Ponce de Leon Avenue', ext='W Trinity Pl to Scott Blvd roundabout', streets=['West Ponce de Leon Avenue'],
      wps=[('West Ponce de Leon Avenue', 'West Trinity Place'), ('West Ponce de Leon Avenue', 'East Parkwood Road')],
      type='protected', phase=1, owner='City', aadt='9,600-11,600 (crash-layer estimate)',
      today='Painted bike lanes outside parking; bike lane drops at W Trinity Pl',
      proposal='Pick Alternative 2 from the city\'s 2026 study: swap parking and bike lanes to make parking-protected lanes with a 3-ft door buffer. Close the gap at W Trinity Pl with a protected merge, which had 2 bike crashes including 1 serious.',
      impact='Low', impactNote='Keeps all lanes and most parking. Narrower lanes slow traffic.',
      serves='St. Thomas More, Adair Park, downtown, Druid Hills'),
 dict(id='C8', name='East Ponce de Leon Avenue', ext='Commerce Dr to Avondale MARTA', streets=['East Ponce de Leon Avenue'],
      wps=[('East Ponce de Leon Avenue', 'Commerce Drive'), ('East Ponce de Leon Avenue', 'Sams Crossing')],
      type='study', phase=3, owner='City', aadt='~23,000 (crash-layer estimate)',
      today='4 lanes, no bike facility',
      proposal='Corridor study, as the Safety Action Plan calls for. Preferred option: 4-to-3 conversion with protected lanes. Fallback: a two-way sidepath on the south side. Phase 1 builds the Glennwood greenway as a parallel low-stress route.',
      impact='Study', impactNote='Close to the upper range for a road diet. Modeling should come first.',
      serves='Glennwood ES, Avondale MARTA, Stone Mountain Trail'),
 dict(id='C9', name='Scott Boulevard shared-use path', ext='W Ponce de Leon Ave to N Decatur Rd', streets=['Scott Boulevard'],
      wps=[('Scott Boulevard', 'West Ponce de Leon Avenue'), ('Scott Boulevard', 'Clairemont Avenue'), ('Scott Boulevard', 'North Decatur Road')],
      type='sidepath', phase=3, owner='GDOT (SR 8)', aadt='~40,000 (crash-layer estimate)',
      today='4 lanes undivided, 40 mph, the most dangerous road in Decatur',
      proposal='Shared-use path and planted median through the RAISE planning grant. Roundabouts or protected intersections at Clairemont Ave and W Ponce de Leon Ave.',
      impact='None', impactNote='The path goes behind the curb, so no lanes are removed. A median and roundabouts slow traffic without cutting capacity.',
      serves='Westchester ES, Clairemont ES, Emory/Druid Hills'),
 dict(id='C10', name='East Lake Drive', ext='W College Ave (East Lake MARTA) to 2nd Ave', streets=['East Lake Drive'],
      wps=[('East Lake Drive', 'West College Avenue'), ('East Lake Drive', '2nd Avenue')],
      type='protected', phase=1, owner='City', aadt='~5,900 (crash-layer estimate)',
      today='Painted bike lanes in places; repaving project under way',
      proposal='Use the 2026 repaving (Park Pl to 2nd Ave) and extend north to W College Ave to upgrade to buffered lanes with flex posts or curb stops. Raised crossings at Oakhurst ES and Spring St, where there was a 2023 bike crash.',
      impact='None', impactNote='The repaving restripes the street anyway, and no lanes are removed.',
      serves='Oakhurst ES, Oakhurst Village, East Lake'),
 dict(id='C11', name='E Trinity Pl / E Howard Ave connector', ext='N McDonough St to Talley St Upper ES', streets=['East Trinity Place', 'East Howard Avenue'],
      wps=[('@', 33.77356, -84.29652, 'East Trinity Place'), ('East Trinity Place', 'East Howard Avenue'), ('@', 33.7700, -84.2850, 'East Howard Avenue')],
      type='protected', phase=2, owner='City', aadt='~14,000 (Trinity), ~2,500 (Howard)',
      today='Downtown couplet; E Howard/E Trinity had 2 bike crashes (1 serious)',
      proposal='One-way protected lanes on E Trinity Pl, a protected intersection at E Howard Ave, and a two-way bikeway on E Howard Ave along the railroad to Agnes Scott.',
      impact='Low', impactNote='Reallocates lane width. E Howard carries low volume.',
      serves='Decatur HS, Agnes Scott College (via S Candler St), Talley St Upper ES'),
 dict(id='C12', name='West Side Connector', ext='Westchester ES to Oakhurst Village', streets=['Adair Street', 'Mead Road'],
      segs=[(('Adair Street', 'West Ponce de Leon Avenue'), ('Adair Street', 'West Howard Avenue'), ['Adair Street']),
            (('Mead Road', 'West College Avenue'), ('Mead Road', 'Oakview Road'), ['Mead Road'])],
      plan=[('Adair Street', 'West Howard Avenue'), ('Mead Road', 'West College Avenue')],
      type='connector', phase=1, owner='City (CSX and GDOT at the crossing)', aadt='Adair ~1,700; Mead ~1,700 (crash-layer estimate)',
      today='No continuous north-south route west of downtown. The railroad and W College Ave block it, and the Atlanta Ave crossing area had 3 bike crashes.',
      proposal="A north-south spine for west Decatur. North of W Ponce it uses the Scott Blvd path (C9) and W Ponce lanes (C7). From the W Ponce/W Trinity merge it runs south as a traffic-calmed greenway on Adair St, past St. Thomas More and Adair Park, to the W Howard cycle track and Stone Mountain Trail. It crosses the CSX tracks at the new Adair St crossing in the city's approved 2019 concept, crosses W College Ave at the new signal, and continues as a greenway on Mead Rd past Oakhurst ES to Oakhurst Village, where it meets the Oakview spine (C4).",
      impact='None', impactNote='Adair St and Mead Rd carry low volumes. The rail crossing and W College signal are already in the city concept. Traffic calming on Adair was funded in 2021-22.',
      serves='Westchester ES, St. Thomas More, Adair Park, Ebster Park, W Howard cycle track, Beacon Hill MS (via W College), Oakhurst ES, Oakhurst Village, East Lake MARTA (via PATH #7)'),
]

SCHOOLS = [  # public (City Schools of Decatur) + private; coords from OSM / Nominatim
 ('Clairemont ES', 33.78256, -84.29612, 'public'), ('Glennwood ES', 33.7762, -84.28971, 'public'),
 ('Westchester ES', 33.78326, -84.30630, 'public'), ('Oakhurst ES', 33.76371, -84.30576, 'public'),
 ('Winnona Park ES', 33.76504, -84.28983, 'public'), ('College Heights ECLC', 33.75763, -84.29711, 'public'),
 ('Talley St Upper ES', 33.76963, -84.28481, 'public'), ('Beacon Hill MS', 33.76769, -84.29944, 'public'),
 ('Decatur HS', 33.77086, -84.29693, 'public'),
 ('St. Thomas More', 33.77317, -84.30492, 'private'), ('Friends School', 33.76155, -84.27702, 'private'),
 ('Waldorf School', 33.76237, -84.27914, 'private'), ('Academe of the Oaks', 33.77157, -84.28403, 'private'),
 ('Agnes Scott College', 33.76889, -84.29445, 'college'), ('Columbia Seminary', 33.76429, -84.28083, 'college'),
]
DEST = [
 ('Decatur Square', 33.77465, -84.29625, 'downtown'), ('Decatur MARTA', 33.77461, -84.29603, 'transit'),
 ('East Lake MARTA', 33.76519, -84.31288, 'transit'), ('Avondale MARTA', 33.77515, -84.28224, 'transit'),
 ('Oakhurst Village', 33.75990, -84.30420, 'village'), ('Legacy Park', 33.76787, -84.27958, 'park'),
 ('Decatur Library', 33.77402, -84.29398, 'civic'), ('Recreation Center', 33.77360, -84.28870, 'civic'),
 ('Glenlake Park', 33.78346, -84.29144, 'park'), ('Ebster Park', 33.77209, -84.30172, 'park'),
 ('McKoy Park', 33.75747, -84.29839, 'park'), ('Dearborn Park', 33.75461, -84.28628, 'park'), ('Adair Park', 33.77213, -84.3055, 'park'),
 ('Suburban Plaza', 33.79020, -84.28780, 'shopping'),
]
SCH = {s[0]: (s[1], s[2]) for s in SCHOOLS}
DST = {d[0]: (d[1], d[2]) for d in DEST}

GREEN = [
 dict(id='G1', name='North Schools Greenway', links=['Clairemont ES', 'Glenlake Park', 'Glennwood ES'], phase=1),
 dict(id='G2', name='South Schools Greenway', links=['Oakhurst ES', 'College Heights ECLC', 'Winnona Park ES'], phase=1),
 dict(id='G3', name='Winnona - Legacy Park Greenway', links=['Winnona Park ES', 'Columbia Seminary', 'Legacy Park'], phase=1),
 dict(id='G4', name='Glennwood - Recreation Center Greenway', links=['Glennwood ES', 'Recreation Center', 'Decatur Library'], phase=1),
 dict(id='G5', name='Westside Greenway', links=['St. Thomas More', 'Ebster Park', 'Decatur HS'], phase=2),
 dict(id='G7', name='East Decatur Greenway (PATH #4)', links=['Dearborn Park', 'Kirk Rd'], phase=2,
      wpts=[(33.75461, -84.28628), ('Midway Road', 'Oldfield Road'), ('Oldfield Road', 'Kirk Road')]),
]

def loc(name):
    return SCH.get(name) or DST.get(name)

out = dict(view=[W, round(H, 1)], corridors=[], greenways=[], mPerUnit=round(M_PER_DEG / SCALE, 4))
proposed_lines = []
CORR_EDGES = set()
for c in CORR:
    c2 = {k: v for k, v in c.items() if k not in ('wps', 'segs', 'plan')}
    if 'segs' in c:
        seqs = [route([X(*a), X(*b)], st) for a, b, st in c['segs']]
        pa, pb = coord[X(*c['plan'][0])], coord[X(*c['plan'][1])]
        L = sum(seq_len_m(q) for q in seqs) + hav(pa, pb)
        c2['d'] = path_d([[coord[n] for n in q] for q in seqs], 0.4)
        c2['dPlan'] = path_d([[pa, pb]], 0.1)
        c2['via'] = [v for q in seqs for v in seq_streets(q)]
        for q in seqs:
            proposed_lines.append((c['id'], [coord[n] for n in q]))
            CORR_EDGES.update(frozenset(e) for e in zip(q, q[1:]))
        proposed_lines.append((c['id'], [pa, pb]))
    else:
        wps = [near(w[1], w[2], [w[3]]) if w[0] == '@' else X(w[0], w[1]) for w in c['wps']]
        seq = route(wps, c['streets'] + ['Scott Boulevard'] if c['id'] == 'C9' else c['streets'])
        L = seq_len_m(seq)
        c2['d'] = path_d(seq_lines(seq), 0.4)
        c2['via'] = seq_streets(seq)
        proposed_lines.append((c['id'], [coord[n] for n in seq]))
        CORR_EDGES.update(frozenset(e) for e in zip(seq, seq[1:]))
    c2['miles'] = round(L / 1609.34, 2)
    out['corridors'].append(c2)
    print(c['id'], c['name'], c2['miles'], 'mi', c2['via'], file=sys.stderr)

for g in GREEN:
    if 'wpts' in g:
        wps = [near_low(*w) if isinstance(w[0], float) else X(*w) for w in g['wpts']]
    else:
        wps = [near_low(la, lo) for la, lo in (loc(n) for n in g['links'])]
    seq = route(wps, mode='greenway')
    runs, cur = [], []
    for a, b in zip(seq, seq[1:]):
        d = G[a][b]
        new = frozenset((a, b)) not in CORR_EDGES and d['hw'] in ('residential', 'unclassified', 'living_street', 'tertiary')
        if new:
            if not cur: cur = [a]
            cur.append(b)
        elif cur:
            runs.append(cur); cur = []
    if cur: runs.append(cur)
    L = sum(seq_len_m(r) for r in runs)
    new_streets = []
    for r in runs:
        for n in seq_streets(r):
            if n not in new_streets: new_streets.append(n)
    g = {k: v for k, v in g.items() if k != 'wpts'}
    g2 = dict(g, miles=round(L / 1609.34, 2), d=path_d([[coord[n] for n in r] for r in runs], 0.4), via=new_streets,
              route=seq_streets(seq), type='greenway')
    out['greenways'].append(g2)
    for r in runs:
        proposed_lines.append((g['id'], [coord[n] for n in r]))
    print(g['id'], g['name'], g2['miles'], 'mi', g2['via'], file=sys.stderr)


STATUS = {
 'C1': ('modify', 'Safety Action Plan 2025 (Clairemont/Commerce safety walk)', 'Recommends evaluating a road diet. Near term: unprotected 5-ft bike lanes with a center turn lane. Later: a buffered cycle track. Not funded or scheduled. The 2026 quick-build only restripes the downtown block at E Ponce.', 'Adds flex-post protection from day one and moves the corridor into Phase 1. Ties the Scott Blvd end to the RAISE study.'),
 'C2': ('endorse', 'Church St & Clairemont quick-build (Feb 2026)', 'Two options: Scenario 1, barrier-protected lanes with a center turn lane; Scenario 2, parking-protected lanes, no turn lane, 9-11 parking spaces added.', 'Picks Scenario 2.'),
 'C3': ('modify', 'Safety Action Plan 2025; PATH #1 built only west of Church St', 'Calls this the HIN segment with the most crashes and no project. Says a road diet is "an appropriate change." No bike facility is specified east of Church St.', 'Adds one-way protected bike lanes to the road diet, plus a protected intersection at N Candler St.'),
 'C4': ('modify', 'PATH plan #2 Agnes Scott Connector and #3 Oakview Rd Connector (2016); Safety Action Plan', 'A two-way cycle track across the tracks on S McDonough, then a 10-ft side path through the Agnes Scott campus to E Davis St, then the Oakview Rd trail west to Oakhurst Village.', "Keeps the Oakview design. Offers an on-street S McDonough route for the middle section in case the campus route (which needs Agnes Scott's agreement) stalls."),
 'C5': ('endorse', 'Safety Action Plan 2025', 'Extend bikeways east from the city limit and East Lake MARTA, with a lane diet and school-zone speed cameras near Beacon Hill MS.', 'Specifies curb or post protection and protected intersections at Atlanta Ave and S McDonough St.'),
 'C6': ('modify', 'GDOT PI 0018335; Safety Action Plan 2025', 'GDOT has programmed a road diet with a protected bike lane from the east city limit west to S Candler St. The Safety Action Plan recommends a protected bikeway along the whole corridor.', "Extends GDOT's project west from S Candler St to S McDonough St and adds a protected intersection at Commerce Dr."),
 'C7': ('endorse', 'W Ponce de Leon Ave Safety Improvements (2026 study)', 'Alternative 1 removes south-side parking to widen the bike lanes. Alternative 2 swaps parking and bike lanes to make parking-protected lanes.', 'Picks Alternative 2 and adds a fix for the bike-lane drop at W Trinity Pl, which the community flagged.'),
 'C8': ('endorse', 'Safety Action Plan 2025', 'Provide a bikeway between Avondale MARTA and downtown, plus speed management.', 'Frames it as a study first (4-to-3 preferred, south-side path as fallback) and adds a parallel greenway in Phase 1.'),
 'C9': ('endorse', 'RAISE planning grant ($1.87M); Safety Action Plan; GDOT PI 0015682 roundabout', 'Shared-use path, tree-lined median, more mid-block crossings, roundabouts or protected intersections.', 'No change.'),
 'C10': ('modify', 'East Lake Dr Maintenance & Safety (2026)', 'Repaving with safety upgrades, Park Pl to 2nd Ave only.', 'Extends north to W College Ave and East Lake MARTA and adds flex posts and raised school crossings.'),
 'C11': ('new', 'Not in any city plan', 'E Trinity Pl is on the High Injury Network, and residents flagged E Howard/E Trinity for sight-line problems. No bikeway has been proposed.', 'New protected link from downtown east along the railroad to Agnes Scott and Talley St Upper ES.'),
 'C12': ('new', 'Not in any city plan; it connects PATH #6, the 2019 Adair St rail-crossing concept, and PATH #3/#7', 'Separate pieces exist: PATH #6 (Westchester ES trail), the approved Adair St rail-crossing concept with a new W College signal, a funded Adair St traffic-calming plan, and PATH #7 (East Lake MARTA greenway). Nothing joins them into a north-south route.', 'New route that ties these pieces into one continuous west-side spine.'),
 'G1': ('modify', 'PATH plan #5 Glennwood Elementary Connector (2016)', 'A trail from Glenlake Park through Decatur Cemetery to Glennwood ES. It needs some land acquisition.', 'Adds an on-street greenway from Clairemont ES to Glennwood ES that needs no land. The cemetery trail stays the long-term goal.'),
 'G2': ('new', 'Safety Action Plan (general Safe Routes to School policy)', 'The plan calls for neighborhood greenways in general but names no route.', 'New school-to-school route linking Oakhurst ES, College Heights and Winnona Park ES.'),
 'G3': ('new', 'Safety Action Plan (general policy)', 'No route named.', 'New route from Winnona Park ES to Columbia Seminary and Legacy Park.'),
 'G4': ('endorse', 'PATH plan #5 Glennwood Elementary Connector (south end)', 'A greenway on Sycamore Pl from Glennwood ES to the Stone Mountain Trail.', 'No change. Extended to the Recreation Center and library.'),
 'G5': ('new', 'Safety Action Plan (Electric Ave speed management)', 'Speed management on Electric Ave near the school recreation facility. No bike route named.', 'New greenway from St. Thomas More and Ebster Park to Decatur HS.'),
 'G6': ('new', 'Not in any city plan', 'None.', 'New link from Oakhurst ES to Beacon Hill MS on Mead Rd and Kings Hwy.'),
 'G7': ('endorse', 'PATH plan #4 East Decatur Connector (2016)', 'A Shoal Creek trail to Dearborn Park, with a greenway on Midway Rd and Oldfield Rd to Kirk Rd.', 'No change. Only the street greenway is drawn; the creek trail needs field alignment.'),
}
for item in out['corridors'] + out['greenways']:
    st, src, city_, chg = STATUS[item['id']]
    item.update(status=st, src=src, city=city_, change=chg)
out['carried'] = [
 dict(n='PATH #6 Westchester ES Connector', d='Paved trails in Hidden Cove Park, the Scott Blvd HAWK crossing, and a creek trail to Garden Ln. Carried forward as a quieter long-term alternative to the Scott Blvd path for the north end of the West Side Connector.'),
 dict(n='PATH #7 East Lake MARTA Connector', d='A neighborhood greenway on Winter Ave, Madison Ave and 1st Ave to Oakview Rd. Carried forward unchanged. It extends the West Side Connector to East Lake MARTA. Not drawn because Winter Ave is missing from the street data.'),
 dict(n='PATH #4 East Decatur Connector (trail)', d='The Shoal Creek trail to Dearborn Park. Carried forward unchanged; only its street greenway is drawn (G7).'),
 dict(n='No right on red downtown', d='The Safety Action Plan prohibits right turns on red at 12 downtown intersections. Supported, and extended to every protected intersection in this proposal.'),
]

# ---------------- basemap ----------------
cls = collections.defaultdict(list)
existing = collections.defaultdict(list)
labels = {}
for w in ways:
    g = w.get('geometry')
    if not g:
        continue
    t = w['tags']; hw = t['highway']
    ln = [(p['lat'], p['lon']) for p in g]
    if not any(inview(a, b) for a, b in ln):
        continue
    k = {'trunk': 'major', 'trunk_link': 'major', 'primary': 'major', 'primary_link': 'major', 'secondary': 'major', 'secondary_link': 'major',
         'tertiary': 'minor', 'tertiary_link': 'minor'}.get(hw, 'local' if hw in ('residential', 'unclassified', 'living_street') else None)
    if hw in ('cycleway',) or (hw == 'path' and t.get('bicycle') in ('yes', 'designated')):
        nm = (t.get('name') or '').lower()
        existing['trail' if ('path' in nm or 'trail' in nm or not nm) else 'track'].append(ln)
    elif any(t.get(x) in ('lane', 'buffered_lane') for x in ('cycleway', 'cycleway:both', 'cycleway:right', 'cycleway:left')):
        existing['lane'].append(ln)
    if k:
        cls[k].append(ln)
out['base'] = {k: path_d(v, 0.8 if k == 'local' else 0.5) for k, v in cls.items()}
out['existing'] = {k: path_d(v, 0.4) for k, v in existing.items()}
out['city'] = path_d([[(p[1], p[0]) for p in city['coordinates'][0]]], 0.5) + 'Z'

# railroad (CSX) for orientation: approximate from OSM? use crash-free constant line along College Ave north side
# HIN lines
hin = [[(p[1], p[0]) for p in f['geometry']['coordinates']] for f in hrn if f['properties']['all_modes_hin_v2'] == 1 and f['geometry']]
hrnl = [[(p[1], p[0]) for p in f['geometry']['coordinates']] for f in hrn if f['properties']['high_risk_network'] == 1 and f['geometry']]
out['hin'] = path_d(hin, 0.5)
out['hrn'] = path_d(hrnl, 0.5)

# ---------------- crashes ----------------
def ptseg(p, a, b):
    # meters, local planar
    ax, ay = (a[1] - p[1]) * COS * M_PER_DEG, (a[0] - p[0]) * M_PER_DEG
    bx, by = (b[1] - p[1]) * COS * M_PER_DEG, (b[0] - p[0]) * M_PER_DEG
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-9
    t = max(0, min(1, -(ax * dx + ay * dy) / L2))
    return math.hypot(ax + t * dx, ay + t * dy)

def dist_to_lines(p, lines):
    return min(ptseg(p, a, b) for ln in lines for a, b in zip(ln, ln[1:]))

all_prop = [ln for _, ln in proposed_lines]
cr = []
for f in crashes:
    pr = f['properties']
    if pr['crash_mode'] not in ('Bike', 'Ped') or not f['geometry']:
        continue
    lon, lat = f['geometry']['coordinates'][:2]
    x, y = P(lat, lon)
    near_m = dist_to_lines((lat, lon), all_prop)
    cr.append(dict(x=x, y=y, m=pr['crash_mode'], s=pr['crash_severity'], yr=pr['col_year'],
                   rd=(pr['primary_road'] or '').title(), xr=(pr['intersecting_road'] or '').title(),
                   mv=pr['veh1_maneuver'] or '', loc=(pr['location_at_impact'] or '').replace('On Roadway - ', ''),
                   sp=pr['speedlimit'], on=near_m <= 40))
out['crashes'] = cr

# ---------------- schools / dest ----------------
exist_lines = []
for w in ways:
    t = w['tags']
    if t['highway'] == 'cycleway' and w.get('geometry'):
        exist_lines.append([(p['lat'], p['lon']) for p in w['geometry']])
sch = []
for n, la, lo, kind in SCHOOLS:
    x, y = P(la, lo)
    sch.append(dict(n=n, x=x, y=y, k=kind, before=round(dist_to_lines((la, lo), exist_lines)),
                    after=round(min(dist_to_lines((la, lo), exist_lines), dist_to_lines((la, lo), all_prop)))))
out['schools'] = sch
out['dest'] = [dict(n=n, x=P(la, lo)[0], y=P(la, lo)[1], k=k) for n, la, lo, k in DEST]

def centre_of(c):
    return coord[X(*c)] if isinstance(c[0], str) else c

SITES = [(d, centre_of(d['centre'])) for d in INTERSECTIONS]
buckets = collections.defaultdict(list)
for f in crashes:
    lon, lat = f['geometry']['coordinates']
    dist, k = min((hav((lat, lon), c), n) for n, (_, c) in enumerate(SITES))
    if dist <= RADIUS_M:
        buckets[k].append(f)

def pct(n, d):
    return round(100 * n / d) if d else 0

out['ints'] = []
for k, (d, c) in enumerate(SITES):
    ps = [f['properties'] for f in buckets[k]]
    vru = [p for p in ps if p['crash_mode'] in ('Bike', 'Ped')]
    x, y = P(*c)
    pts = []
    for f in buckets[k]:
        p = f['properties']
        lon, lat = f['geometry']['coordinates']
        px, py = P(lat, lon)
        pts.append([px, py, {'Bike': 'b', 'Ped': 'p'}.get(p['crash_mode'], 'v'), 1 if p['crash_severity'] in ('K', 'A') else 0])
    manner = collections.Counter(p['manner_collision'] for p in ps).most_common(2)
    st = dict(total=len(ps), bike=sum(p['crash_mode'] == 'Bike' for p in ps), ped=sum(p['crash_mode'] == 'Ped' for p in ps),
              fsi=sum(p['crash_severity'] in ('K', 'A') for p in ps), fatal=sum(p['crash_severity'] == 'K' for p in ps),
              vru=len(vru), vru_fsi=sum(p['crash_severity'] in ('K', 'A') for p in vru),
              vru_left=sum('Left' in p['veh1_maneuver'] for p in vru), vru_right=sum('Right' in p['veh1_maneuver'] for p in vru),
              vru_dark=sum('Dark' in p['lighting_condition'] for p in vru),
              dark_pct=pct(sum('Dark' in p['lighting_condition'] for p in ps), len(ps)),
              left_pct=pct(sum('Left' in p['veh1_maneuver'] for p in ps), len(ps)),
              hit_run=sum(p['hit_and_run'] for p in ps), top=[m for m, _ in manner])
    out['ints'].append(dict(id=d['id'], n=d['name'], x=x, y=y, lat=round(c[0], 5), lon=round(c[1], 5), context=d['context'],
                            issues=d['issues'], routes=d['routes'], st=st, pts=pts,
                            fixes=[dict(fix=f, addr=a_, ev=EVIDENCE[e], k=e) for f, a_, e in d['fixes']]))
# rank: most walking/biking crashes first, then most serious
out['ints'].sort(key=lambda i: (-i['st']['vru'], -i['st']['vru_fsi'], -i['st']['total']))

# lane-level plan diagrams, today and as proposed (src/diagrams.py, src/layouts.py)
osm_x = json.load(open(os.path.join(SNAP, 'osm_intersections.json'), encoding='utf-8'))['elements']
lay = {L['id']: L for L in LAYOUTS}
for i in out['ints']:
    L = lay.get(i['id'])
    if L:
        i['dg'] = dict(now=diagrams.render_site(osm_x, L, 'now'), new=diagrams.render_site(osm_x, L, 'new'),
                       aspect=round(L['half'][1] / L['half'][0], 3))
print('diagrams', sum(len(i.get('dg', {}).get('now', '')) + len(i.get('dg', {}).get('new', '')) for i in out['ints']) // 1024, 'KB', file=sys.stderr)
for n, i in enumerate(out['ints'], 1):
    i['rank'] = n
allvru = [f for f in crashes if f['properties']['crash_mode'] in ('Bike', 'Ped')]
out['intsum'] = dict(n=len(out['ints']), radius_ft=round(RADIUS_M * 3.28084 / 10) * 10,
                     vru=sum(i['st']['vru'] for i in out['ints']), vru_all=len(allvru),
                     vru_fsi=sum(i['st']['vru_fsi'] for i in out['ints']),
                     vru_fsi_all=sum(f['properties']['crash_severity'] in ('K', 'A') for f in allvru),
                     vru_left=sum(i['st']['vru_left'] for i in out['ints']),
                     vru_dark=sum(i['st']['vru_dark'] for i in out['ints']),
                     total=sum(i['st']['total'] for i in out['ints']), total_all=len(crashes))
for i in out['ints']:
    print(i['rank'], i['id'], i['n'], i['st'], file=sys.stderr)
print(out['intsum'], file=sys.stderr)

# ---------------- metrics ----------------
def summarize(mode):
    s = [c for c in cr if c['m'] == mode]
    return dict(total=len(s), fsi=sum(c['s'] in ('K', 'A') for c in s), on=sum(c['on'] for c in s),
                fsi_on=sum(c['on'] and c['s'] in ('K', 'A') for c in s))
pub = [s for s in sch if s['k'] == 'public']
out['metrics'] = dict(
    bike=summarize('Bike'), ped=summarize('Ped'),
    public_schools=len(pub),
    pub_before=sum(s['before'] <= 400 for s in pub), pub_after=sum(s['after'] <= 400 for s in pub),
    miles=dict(protected=round(sum(c['miles'] for c in out['corridors'] if c['type'] == 'protected'), 1),
               sidepath=round(sum(c['miles'] for c in out['corridors'] if c['type'] == 'sidepath'), 1),
               connector=round(sum(c['miles'] for c in out['corridors'] if c['type'] == 'connector'), 1),
               study=round(sum(c['miles'] for c in out['corridors'] if c['type'] == 'study'), 1),
               greenway=round(sum(g['miles'] for g in out['greenways']), 1)),
    existing_miles=round(sum(seq for seq in [sum(hav(a, b) for a, b in zip(l, l[1:])) for l in exist_lines]) / 1609.34, 1),
)
print(json.dumps(out['metrics'], indent=1), file=sys.stderr)
for s in sch:
    print(s['n'], s['before'], s['after'], file=sys.stderr)
json.dump(out, open(os.path.join(DATA, 'network.json'), 'w', encoding='utf-8'), separators=(',', ':'))

with open(os.path.join(DATA, 'intersections.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['rank', 'id', 'intersection', 'lat', 'lon', 'all_crashes', 'bike_crashes', 'ped_crashes', 'fatal_or_serious_all_modes',
                'fatal', 'bike_ped_fatal_or_serious', 'bike_ped_driver_turning_left', 'bike_ped_driver_turning_right', 'bike_ped_after_dark',
                'pct_all_after_dark', 'hit_and_run', 'most_common_crash_types', 'proposed_fixes'])
    for i in out['ints']:
        t = i['st']
        w.writerow([i['rank'], i['id'], i['n'], i['lat'], i['lon'], t['total'], t['bike'], t['ped'], t['fsi'], t['fatal'], t['vru_fsi'],
                    t['vru_left'], t['vru_right'], t['vru_dark'], t['dark_pct'], t['hit_run'], '; '.join(t['top']),
                    ' | '.join(f['fix'] for f in i['fixes'])])

with open(os.path.join(DATA, 'bike_ped_crashes_2019_2023.csv'), 'w', newline='', encoding='utf-8') as fh:
    cols = list(allvru[0]['properties'].keys())
    w = csv.writer(fh)
    w.writerow(cols)
    for f in allvru:
        w.writerow([f['properties'][c] for c in cols])

page = open(os.path.join(ROOT, 'src', 'template.html'), encoding='utf-8').read().replace(
    '__DATA__', json.dumps(out, separators=(',', ':'), ensure_ascii=False))
open(os.path.join(ROOT, 'decatur-connects.html'), 'w', encoding='utf-8').write(page)
os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
open(os.path.join(ROOT, 'docs', 'index.html'), 'w', encoding='utf-8').write(
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n'
    + page + '\n</body>\n</html>\n')
print('built docs/index.html', os.path.getsize(os.path.join(ROOT, 'docs', 'index.html')), 'bytes', file=sys.stderr)
