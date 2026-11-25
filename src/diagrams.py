"""Lane-level plan diagrams of each priority intersection, today and as proposed.

Streets are drawn along their real OpenStreetMap centerlines, so angles and curves match the
ground. Each street segment gets a cross-section (lanes, bike lanes, buffers, parking, medians,
sidewalks) written in src/layouts.py and checked against aerial imagery.

Cross-section strings list elements LEFT to RIGHT relative to the OSM way's drawing direction:

    sw  grass  curb  med  bfr  post  pk  tw  path  ct2  dw  pmed   (widths in feet: sw@8)
    dw = unmarked paved driveway/service road; pmed = painted (hatched yellow) median
    >T  <L  >TR  >  <          car lanes: > forward, < backward, letters = arrow painted
    bl> bl<                    painted bike lane
    cb> cb<                    curb-protected one-way bike lane
    ct2                        two-way cycle track
"""
import math, re
from shapely.geometry import LineString, Point, Polygon, MultiPolygon, MultiLineString, box
from shapely.ops import unary_union, linemerge

FT = 0.3048
DEF_W = {'sw': 6, 'grass': 4, 'curb': 2, 'med': 6, 'bfr': 3, 'post': 3, 'pk': 8, 'tw': 11, 'path': 12, 'ct2': 10,
         'lane': 11, 'bl': 5, 'cb': 6, 'gut': 1.5, 'dw': 22, 'pmed': 4}
PAVED = {'lane', 'tw', 'bl', 'bfr', 'post', 'pk', 'gut', 'dw', 'pmed'}
CAR = {'lane', 'tw'}

C = dict(  # colours are CSS variables defined in the page template
    land='var(--dg-land)', walk='var(--dg-walk)', grass='var(--dg-grass)', road='var(--dg-road)', park='var(--dg-park)',
    bike='var(--dg-bike)', bikeline='var(--dg-bikeline)', isl='var(--dg-isl)', white='var(--dg-white)', yellow='var(--dg-yellow)',
    rail='var(--dg-rail)', path='var(--dg-path)', label='var(--dg-label)', halo='var(--dg-halo)', call='var(--dg-call)',
    raised='var(--dg-raised)', new='var(--dg-new)')


def parse_xs(spec):
    out = []
    for tok in spec.split():
        if tok == 'unmarked':
            continue
        w = None
        if '@' in tok:
            tok, ws = tok.split('@')
            w = float(ws)
        m = re.fullmatch(r'([<>])([LTRU]*)', tok)
        if m:
            out.append(dict(k='lane', d=1 if m.group(1) == '>' else -1, turn=m.group(2), w=(w or DEF_W['lane']) * FT))
            continue
        m = re.fullmatch(r'(bl|cb)([<>])', tok)
        if m:
            out.append(dict(k=m.group(1), d=1 if m.group(2) == '>' else -1, w=(w or DEF_W[m.group(1)]) * FT))
            continue
        if tok == 'yy':
            out.append(dict(k='yy', w=0))
            continue
        if tok not in DEF_W:
            raise ValueError(f'unknown cross-section token {tok!r} in {spec!r}')
        out.append(dict(k=tok, w=(w or DEF_W[tok]) * FT))
    return out


class Proj:
    def __init__(self, lat0, lon0):
        self.lat0, self.lon0, self.c = lat0, lon0, math.cos(math.radians(lat0))

    def __call__(self, lat, lon):
        return ((lon - self.lon0) * self.c * 111320.0, -(lat - self.lat0) * 111320.0)


def fmt(v):
    r = f'{v:.1f}'.rstrip('0').rstrip('.')
    return '0' if r in ('-0', '') else r


def path_d(geom):
    """SVG path data for a shapely geometry (polygons with holes, lines)."""
    if geom is None or geom.is_empty:
        return ''
    t = geom.geom_type
    if t in ('MultiPolygon', 'GeometryCollection', 'MultiLineString'):
        return ''.join(path_d(g) for g in geom.geoms)
    if t == 'Polygon':
        rings = [geom.exterior] + list(geom.interiors)
        return ''.join('M' + 'L'.join(f'{fmt(x)},{fmt(y)}' for x, y in r.coords[:-1]) + 'Z' for r in rings)
    if t in ('LineString', 'LinearRing'):
        return 'M' + 'L'.join(f'{fmt(x)},{fmt(y)}' for x, y in geom.coords)
    return ''


def strip(line, a, b):
    """Polygon between offsets a and b (metres, positive = real-world left of the line's direction)."""
    if abs(a - b) < 1e-6:
        return None
    # offsets are measured to the real-world left of travel. With SVG's y axis pointing down that is
    # shapely's negative side, hence the sign flip.
    la = line.offset_curve(-a) if abs(a) > 1e-6 else line
    lb = line.offset_curve(-b) if abs(b) > 1e-6 else line
    if la.is_empty or lb.is_empty or la.geom_type != 'LineString' or lb.geom_type != 'LineString':
        return line.buffer(abs(a - b) / 2, cap_style='flat').buffer(0)
    p = Polygon(list(la.coords) + list(lb.coords)[::-1])
    return p.buffer(0)


def offset_line(line, o):
    if abs(o) < 1e-6:
        return line
    r = line.offset_curve(-o)
    return r if r.geom_type == 'LineString' else None


def extend(line, e=0.4):
    """Extend a polyline a little at both ends so neighbouring segments overlap."""
    c = list(line.coords)
    (x0, y0), (x1, y1) = c[0], c[1]
    L = math.hypot(x1 - x0, y1 - y0) or 1
    c[0] = (x0 - (x1 - x0) / L * e, y0 - (y1 - y0) / L * e)
    (x0, y0), (x1, y1) = c[-1], c[-2]
    L = math.hypot(x1 - x0, y1 - y0) or 1
    c[-1] = (x0 - (x1 - x0) / L * e, y0 - (y1 - y0) / L * e)
    return LineString(c)


def arrow_glyph(turn):
    """Arrow outline polylines in a local frame: origin at arrow tail, +y = direction of travel, metres."""
    shaft = [(0, 0), (0, 3.2)]
    head = lambda x, y, ang: [(x + 0.55 * math.cos(ang + 2.5), y + 0.55 * math.sin(ang + 2.5)), (x, y),
                              (x + 0.55 * math.cos(ang - 2.5), y + 0.55 * math.sin(ang - 2.5))]
    parts = []
    if 'T' in turn or turn == '':
        parts += [[(0, 0), (0, 4.4)], head(0, 4.4, math.pi / 2)]
    else:
        parts.append(shaft)
    if 'L' in turn:  # vehicle turning left: +x is the driver's right in this frame, so left is -x
        parts += [[(0, 2.4), (0, 3.2), (-0.35, 3.75), (-1.15, 3.85)], head(-1.15, 3.85, math.pi)]
    if 'R' in turn:
        parts += [[(0, 2.4), (0, 3.2), (0.35, 3.75), (1.15, 3.85)], head(1.15, 3.85, 0)]
    if 'U' in turn:
        parts += [[(0, 2.6), (0, 3.6), (-0.5, 4.1), (-1.0, 3.6), (-1.0, 2.6)], head(-1.0, 2.6, -math.pi / 2)]
    return parts


class Site:
    """One diagram: a set of OSM ways with cross-sections, clipped to a frame."""

    def __init__(self, osm_ways, osm_nodes, layout, mode):
        self.L, self.mode = layout, mode
        self.P = Proj(*layout['center'])
        hw, hh = layout.get('half', (45, 45))
        self.frame = box(-hw, -hh, hw, hh)
        self.big = box(-hw - 30, -hh - 30, hw + 30, hh + 30)
        self.osm_ways, self.osm_nodes = osm_ways, osm_nodes
        self.callouts = []

    # ---------------- geometry helpers ----------------
    def way_line(self, wid):
        w = self.osm_ways[wid]
        return LineString([self.P(p['lat'], p['lon']) for p in w['geometry']])

    def node_xy(self, nid):
        n = self.osm_nodes[nid]
        return self.P(n['lat'], n['lon'])

    def xs_for(self, wid):
        spec = self.ways_spec[wid]
        if isinstance(spec, dict):
            s = spec.get(self.mode, spec.get('now'))
        else:
            s = spec
        return s

    def layout_xs(self, wid):
        """Elements with left/right offsets (m, + = left of the way's direction)."""
        s = self.xs_for(wid)
        if s is None:
            return None, (0, 0)
        if isinstance(s, tuple):
            s, shift = s
        else:
            shift = 0.0
        els = parse_xs(s)
        pos, x = [], 0.0
        for e in els:
            pos.append((x, x + e['w']))
            x += e['w']
        paved = [i for i, e in enumerate(els) if e['k'] in PAVED]
        if paved:
            lo, hi = pos[paved[0]][0], pos[paved[-1]][1]
        else:
            lo, hi = 0, x
        mid = (lo + hi) / 2
        # left-to-right list -> offsets: leftmost element has the largest positive offset
        for e, (a, b) in zip(els, pos):
            e['oL'] = mid - a + shift
            e['oR'] = mid - b + shift
        return els, (mid - lo + shift, mid - hi + shift)

    # ---------------- build ----------------
    def build(self):
        L = self.L
        self.segs = []
        self.ways_spec = dict(L['ways'])
        for aw in L.get('add_ways', []):
            if self.mode not in aw.get('modes', ('now', 'new')):
                continue
            pts = [self.osm_nodes[aw['nodes'][0]]] + [dict(lat=a, lon=b) for a, b in aw.get('via', [])] + [self.osm_nodes[aw['nodes'][-1]]]
            self.osm_ways[aw['id']] = dict(id=aw['id'], nodes=[aw['nodes'][0]] + [f"{aw['id']}_{i}" for i in range(len(aw.get('via', [])))] + [aw['nodes'][-1]],
                                           geometry=[dict(lat=q['lat'], lon=q['lon']) for q in pts], tags={})
            self.ways_spec[aw['id']] = aw['spec']
        for wid in self.ways_spec:
            if wid not in self.osm_ways:
                raise KeyError(f"{L['id']}: way {wid} not in OSM snapshot")
            els, (cl, cr) = self.layout_xs(wid)
            if els is None:
                continue
            line = extend(self.way_line(wid))
            raw = self.xs_for(wid)
            raw = raw[0] if isinstance(raw, tuple) else raw
            self.segs.append(dict(wid=wid, line=line, els=els, cl=cl, cr=cr, nodes=self.osm_ways[wid]['nodes'],
                                  unmarked='unmarked' in raw.split()))
        # junction nodes: shared by two or more drawn segments, or interior node used by another segment
        cnt = {}
        for s in self.segs:
            for i, n in enumerate(s['nodes']):
                cnt.setdefault(n, set()).add(s['wid'])
        self.junctions = {}
        for n, ws in cnt.items():
            deg = 0
            for s in self.segs:
                if s['wid'] in ws:
                    ns = s['nodes']
                    deg += 1 if n in (ns[0], ns[-1]) else 2
            if deg >= 3 and n not in L.get('not_junction', []):
                self.junctions[n] = self.node_xy(n)
        for n in L.get('junctions', []):
            self.junctions[n] = self.node_xy(n)
        # car-lane area per segment and paved area
        paved, car, raised, walks, grass, bikes, parks, bufs, posts, tws, paths, pmeds = ([] for _ in range(12))
        for s in self.segs:
            for e in s['els']:
                p = strip(s['line'], e['oL'], e['oR'])
                if p is None:
                    continue
                k = e['k']
                if k in PAVED:
                    paved.append(p)
                if k in CAR:
                    car.append(p)
                if k == 'sw':
                    walks.append(p)
                elif k == 'grass':
                    grass.append(p)
                elif k in ('curb', 'med'):
                    raised.append(p)
                elif k in ('bl', 'cb', 'ct2'):
                    bikes.append((p, k, s, e))
                elif k == 'pk':
                    parks.append(p)
                elif k == 'bfr':
                    bufs.append(p)
                elif k == 'post':
                    posts.append((p, s, e))
                elif k == 'tw':
                    tws.append(p)
                elif k == 'path':
                    paths.append(p)
                elif k == 'pmed':
                    pmeds.append(p)
        r = L.get('corner_r', {}).get(self.mode, L.get('corner_r', {}).get('now', 7.5)) if isinstance(L.get('corner_r'), dict) else L.get('corner_r', 7.5)
        self.r = r
        road = unary_union(paved)
        self.road_raw = road
        road = road.buffer(r, join_style='round').buffer(-r, join_style='round')
        for f in self.features('fill_road'):
            road = road.union(f['geom'])
        for f in self.features('cut_road'):
            road = road.difference(f['geom'])
        self.road = road.intersection(self.big)
        self.car = unary_union(car)
        self.car_by_seg = []
        for sg in self.segs:
            cs = [strip(sg['line'], e['oL'], e['oR']) for e in sg['els'] if e['k'] in CAR]
            cs = [g for g in cs if g is not None]
            if cs:
                self.car_by_seg.append((sg, unary_union(cs).buffer(0.3)))
        self.raised, self.walks, self.grass = unary_union(raised), unary_union(walks), unary_union(grass)
        self.bikes, self.parks, self.bufs, self.posts, self.tws, self.paths = bikes, unary_union(parks), unary_union(bufs), posts, unary_union(tws), unary_union(paths)
        self.pmeds = unary_union(pmeds)
        for gp in L.get('gapfill', []):
            if self.mode not in gp.get('modes', ('now', 'new')):
                continue
            parts = [sg for sg in self.segs if sg['wid'] in gp['ways']]
            pv = unary_union([strip(sg['line'], max(e['oL'] for e in sg['els'] if e['k'] in PAVED),
                                    min(e['oR'] for e in sg['els'] if e['k'] in PAVED)) for sg in parts])
            gap = pv.buffer(gp.get('r', 6)).buffer(-gp.get('r', 6)).difference(pv)
            if 'clip' in gp:
                gap = gap.intersection(Polygon([self.ll(q) for q in gp['clip']]))
            self.pmeds = self.pmeds.union(gap)
            self.road = self.road.union(gap)
        # junction zones: circle reaching just past the widest carriageway meeting there
        self.zones = {}
        for n, (x, y) in self.junctions.items():
            half = 0
            for s in self.segs:
                if n in s['nodes']:
                    cw = [e for e in s['els'] if e['k'] in PAVED]
                    if cw:
                        half = max(half, max(abs(e['oL']) for e in cw), max(abs(e['oR']) for e in cw))
            zr = half + 0.8
            for it in self.crossing_items_raw():
                d = it['line'].distance(Point(x, y))
                if d < 25 and it['style'] != 'bike':
                    zr = max(zr, d - 1.5)
            self.zones[n] = Point(x, y).buffer(L.get('zone_r', {}).get(n, zr))
        self.zone_union = unary_union(list(self.zones.values())) if self.zones else Polygon()
        if not self.parks.is_empty:
            self.parks = self.parks.difference(self.zone_union.buffer(self.L.get('daylight', 6.0)))
        self.extra_xings, self.rings, self.islands_p, self.pcircles = [], [], [], []
        if self.mode == 'new':
            for pi in self.L.get('protected', []):
                self.build_protected(pi)
        return self

    def build_protected(self, pi):
        """Protected intersection. Inside a radius of the junction, each arm's bike lane bends away
        from the travel lanes to a set-back (default 15 ft), leaving concrete corner islands between
        the bike ring and tightened car corners. Bike crossings sit where the set-back bike lanes of
        the neighbouring arms cross each arm; the crosswalk sits just outside them."""
        cx, cy = self.ll(pi['at'])
        if self.junctions:
            n, (cx, cy) = min(self.junctions.items(), key=lambda kv: math.hypot(kv[1][0] - cx, kv[1][1] - cy))
        c = Point(cx, cy)
        rc = pi.get('r', 3.5)
        S = pi.get('setback', 4.5)
        r1 = pi.get('r_ring', 6.5)
        arms = []
        for sg in self.segs:
            if sg['line'].distance(c) > 3:
                continue
            els = sg['els']
            ce = [e for e in els if e['k'] in CAR]
            if not ce:
                continue
            ci = [i for i, e in enumerate(els) if e['k'] in CAR]
            bk = [i for i, e in enumerate(els) if e['k'] in ('bl', 'cb', 'ct2', 'path')]
            lb = max([i for i in bk if i < ci[0]], default=None)
            rb = min([i for i in bk if i > ci[-1]], default=None)
            line = sg['line']
            t0 = line.project(c)
            for sgn in (1, -1):
                if not (0 <= t0 + sgn * 8 <= line.length):
                    continue
                arms.append(dict(s=sg, line=line, t0=t0, sgn=sgn, oLc=max(e['oL'] for e in ce), oRc=min(e['oR'] for e in ce),
                                 bwL=els[lb]['w'] if lb is not None else None, bwR=els[rb]['w'] if rb is not None else None,
                                 baseL=(els[lb]['oR'] - max(e['oL'] for e in ce)) if lb is not None else None,
                                 baseR=(min(e['oR'] for e in ce) - els[rb]['oL']) if rb is not None else None))
        if not arms:
            return
        bw0 = pi.get('bw', 2.0)

        def tangent(line, t):
            a_ = line.interpolate(max(0, t - 0.4))
            b_ = line.interpolate(min(line.length, t + 0.4))
            L = math.hypot(b_.x - a_.x, b_.y - a_.y) or 1
            return (b_.x - a_.x) / L, (b_.y - a_.y) / L

        def car_half(a):
            return max(abs(a['oLc']), abs(a['oRc']))

        def var_strip(a, f_off1, f_off2, t_end):
            pts1, pts2 = [], []
            k = 0.0
            while k <= t_end + 1e-6:
                t = a['t0'] + a['sgn'] * k
                if t < 0 or t > a['line'].length:
                    break
                q = a['line'].interpolate(t)
                dx, dy = tangent(a['line'], t)
                nx, ny = dy, -dx
                o1, o2 = f_off1(k), f_off2(k)
                pts1.append((q.x + nx * o1, q.y + ny * o1))
                pts2.append((q.x + nx * o2, q.y + ny * o2))
                k += 0.5
            if len(pts1) < 2:
                return Polygon()
            return Polygon(pts1 + pts2[::-1]).buffer(0)

        # where each arm reaches its full set-back, and where the taper back to normal ends
        for a in arms:
            others = [b for b in arms if b['s'] is not a['s']]
            reach = max([car_half(b) for b in others], default=car_half(a))
            a['t1'] = reach + S + max(a['bwL'] or bw0, a['bwR'] or bw0) + 4.5
            a['t2'] = a['t1'] + pi.get('taper', 14)

        def w(a, k):
            if k <= a['t1']:
                return 1.0
            if k >= a['t2']:
                return 0.0
            return 1 - (k - a['t1']) / (a['t2'] - a['t1'])

        cars, inners, outers, bikecl = [], [], [], []
        Rcut = max(a['t2'] for a in arms) + 1
        for a in arms:
            oL, oR = a['oLc'], a['oRc']
            car = var_strip(a, lambda k: oL, lambda k: oR, a['t2'] + 2)
            cars.append(car)
            # left side
            if a['bwL'] is not None:
                bL, bwL = a['baseL'], a['bwL']
                sepL = lambda k, a=a, bL=bL: bL + (S - bL) * w(a, k)
                inners.append(var_strip(a, lambda k: oL + sepL(k), lambda k: oL, a['t2']))
                outers.append(var_strip(a, lambda k: oL + sepL(k) + bwL, lambda k: oL, a['t2']))
                bikecl.append((a, lambda k, sepL=sepL, bwL=bwL: oL + sepL(k) + bwL / 2))
            else:
                inners.append(var_strip(a, lambda k: oL + S, lambda k: oL, a['t1']))
                outers.append(var_strip(a, lambda k: oL + S + bw0, lambda k: oL, a['t1']))
                bikecl.append((a, lambda k: oL + S + bw0 / 2))
            # right side
            if a['bwR'] is not None:
                bR, bwR = a['baseR'], a['bwR']
                sepR = lambda k, a=a, bR=bR: bR + (S - bR) * w(a, k)
                inners.append(var_strip(a, lambda k: oR, lambda k: oR - sepR(k), a['t2']))
                outers.append(var_strip(a, lambda k: oR, lambda k: oR - sepR(k) - bwR, a['t2']))
                bikecl.append((a, lambda k, sepR=sepR, bwR=bwR: oR - sepR(k) - bwR / 2))
            else:
                inners.append(var_strip(a, lambda k: oR, lambda k: oR - S, a['t1']))
                outers.append(var_strip(a, lambda k: oR, lambda k: oR - S - bw0, a['t1']))
                bikecl.append((a, lambda k: oR - S - bw0 / 2))
        circ = c.buffer(Rcut)
        Kc = unary_union(cars).buffer(rc, join_style='round').buffer(-rc, join_style='round')
        Sep = unary_union(inners).buffer(r1, join_style='round').buffer(-r1, join_style='round')
        Bike = unary_union(outers).buffer(r1, join_style='round').buffer(-r1, join_style='round')
        allcars = unary_union(cars)
        ring = Bike.difference(Sep).difference(allcars)
        isl = Sep.difference(Kc).difference(allcars)
        box_r = max(car_half(a) for a in arms) + 1.0
        self.zone_union = self.zone_union.union(Kc.intersection(c.buffer(box_r * 1.5)))
        self.road = self.road.difference(Bike.union(circ.intersection(Sep))).union(Kc.intersection(circ))
        self.rings.append(ring)
        self.islands_p.append(isl)
        self.pcircles.append((c, Rcut, Bike))
        # bike crossings: where the neighbouring arms' set-back bike lanes cross this arm
        skip = pi.get('skip', [])
        for a in arms:
            if a['s']['wid'] in skip:
                continue
            ux, uy = tangent(a['line'], a['t0'] + a['sgn'] * 6)
            ux, uy = ux * a['sgn'], uy * a['sgn']
            axis = LineString([(cx, cy), (cx + ux * 40, cy + uy * 40)])
            ts = []
            for b, f in bikecl:
                if b['s'] is a['s']:
                    continue
                pts = []
                k = 0.0
                while k <= b['t1'] + 6:
                    t = b['t0'] + b['sgn'] * k
                    if t < 0 or t > b['line'].length:
                        break
                    q = b['line'].interpolate(t)
                    dx, dy = tangent(b['line'], t)
                    o = f(k)
                    pts.append((q.x + dy * o, q.y - dx * o))
                    k += 0.5
                # extend the bike centreline back through the junction so it can cross this arm
                if len(pts) >= 2:
                    (x0, y0), (x1, y1) = pts[0], pts[1]
                    L = math.hypot(x0 - x1, y0 - y1) or 1
                    pts.insert(0, (x0 + (x0 - x1) / L * 30, y0 + (y0 - y1) / L * 30))
                    hit = LineString(pts).intersection(axis)
                    for g in getattr(hit, 'geoms', [hit]):
                        if not g.is_empty and g.geom_type == 'Point':
                            ts.append((g.x - cx) * ux + (g.y - cy) * uy)
            bw = max(a['bwL'] or bw0, a['bwR'] or bw0)
            tb = max(ts) if ts else car_half(a) + S + bw / 2
            tp = tb + bw / 2 + 0.8 + 1.5
            q = a['line'].interpolate(a['t0'] + a['sgn'] * tb)
            dx, dy = tangent(a['line'], a['t0'] + a['sgn'] * tb)
            nx, ny = dy, -dx
            for t, st in ((tb, 'bike'), (tp, pi.get('xing', 'ladder'))):
                q = a['line'].interpolate(a['t0'] + a['sgn'] * t)
                ww = car_half(a) + 0.3
                self.extra_xings.append(dict(line=LineString([(q.x + nx * (a['oLc'] + 0.2), q.y + ny * (a['oLc'] + 0.2)),
                                                              (q.x + nx * (a['oRc'] - 0.2), q.y + ny * (a['oRc'] - 0.2))]), style=st))

    def features(self, kind):
        out = []
        for f in self.L.get('features', []):
            if f['type'] != kind or self.mode not in f.get('modes', ('now', 'new')):
                continue
            g = self.feature_geom(f)
            out.append(dict(f, geom=g))
        return out

    def ll(self, p):
        if isinstance(p, dict):
            return p['xy']
        return self.P(*p) if isinstance(p, (tuple, list)) and abs(p[0]) > 20 else p

    def feature_geom(self, f):
        if 'poly' in f:
            return Polygon([self.ll(p) for p in f['poly']]).buffer(0)
        if 'line' in f:
            return LineString([self.ll(p) for p in f['line']])
        if 'circle' in f:
            (c, rad) = f['circle']
            return Point(self.ll(c)).buffer(rad)
        if 'at' in f:
            return Point(self.ll(f['at']))
        if 'link' in f:  # band joining points on two ways, e.g. a bike lane carried through a junction
            pts = []
            for wid, node, d, tok, idx in f['link']:
                line, t, (dx, dy), sgn = self.station(wid, node, d)
                q = line.interpolate(t)
                oa, ob = self.offsets(wid, tok, idx)
                o = (oa + ob) / 2
                pts.append((q.x + dy * o, q.y - dx * o))
            return LineString(pts).buffer(f.get('w', 1.8) / 2, cap_style='flat')
        if 'node' in f and 'way' in f:  # strip along a way between d0 and d1 metres from a node
            line, t0, _, sgn = self.station(f['way'], f['node'], 0)
            d0, d1 = f['d']
            a, b = sorted((t0 + sgn * d0, t0 + sgn * d1))
            sub = substring(line, max(0, a), min(line.length, b))
            if 'o' in f:
                oa, ob = f['o']
            else:
                oa, ob = self.offsets(f['way'], f.get('token'), f.get('idx', 0))
                if f.get('token') == 'yy':
                    oa, ob = oa + f.get('w', 0.7) / 2, oa - f.get('w', 0.7) / 2
            ins = f.get('inset', 0.0)
            return strip(sub, oa - ins, ob + ins)
        if 'near' in f and 'way' in f:  # island centred on a point, aligned with a way, inside one cross-section element
            line = self.way_line(f['way'])
            els, _ = self.layout_xs(f['way'])
            e = [e for e in els if e['k'] == f.get('token', 'tw')][0]
            t = line.project(Point(self.ll(f['near'])))
            sub = substring(line, max(0, t - f['length'] / 2), min(line.length, t + f['length'] / 2))
            ins = f.get('inset', 0.3)
            return strip(sub, e['oL'] - ins, e['oR'] + ins)
        if 'way' in f:  # region along a way: (s0, s1) metres from its first node, offsets (a, b)
            line = self.way_line(f['way'])
            s0, s1 = f['s']
            sub = substring(line, s0, s1)
            return strip(sub, f['o'][0], f['o'][1])
        return None

    # ---------------- render ----------------
    def render(self, title=None):
        out = []
        add = out.append
        hw, hh = self.L.get('half', (45, 45))
        clipid = f"dgc-{self.L['id']}-{self.mode}"
        add(f'<svg viewBox="{-hw} {-hh} {2 * hw} {2 * hh}" class="dg" role="img" aria-label="{title or ""}">')
        add(f'<defs><clipPath id="{clipid}"><rect x="{-hw}" y="{-hh}" width="{2 * hw}" height="{2 * hh}"/></clipPath>'
            f'<pattern id="hatch-{clipid}" width="1.2" height="1.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="1.2" height="1.2" fill="{C["road"]}"/><rect width="0.35" height="1.2" fill="{C["white"]}"/></pattern>'
            f'<pattern id="yhatch-{clipid}" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="1.6" height="1.6" fill="{C["road"]}"/><rect width="0.35" height="1.6" fill="{C["yellow"]}"/></pattern></defs>')
        add(f'<g clip-path="url(#{clipid})">')
        add(f'<rect x="{-hw}" y="{-hh}" width="{2 * hw}" height="{2 * hh}" fill="{C["land"]}"/>')
        # sidewalks: explicit strips plus a band around every curb so corners close
        walk = unary_union([self.walks, self.road.buffer(1.8, join_style='round').difference(self.road)] +
                           [o.buffer(1.8).intersection(c.buffer(r + 1.8)) for c, r, o in self.pcircles])
        for f in self.features('walk'):
            walk = walk.union(f['geom'])
        walk = walk.intersection(self.big)
        add(f'<path d="{path_d(self.grass)}" fill="{C["grass"]}"/>')
        add(f'<path d="{path_d(walk)}" fill="{C["walk"]}"/>')
        # off-street paths and cycle tracks from OSM (drawn below the road)
        for f in self.L.get('osm_paths', []):
            if self.mode not in f.get('modes', ('now', 'new')):
                continue
            g = unary_union([self.way_line(w) for w in f['ways']]).buffer(f.get('w', 3.0) / 2, cap_style='flat')
            add(f'<path d="{path_d(g.difference(self.road))}" fill="{C["bike"] if f.get("bike") else C["path"]}"/>')
        for p in self.paths.geoms if hasattr(self.paths, 'geoms') else [self.paths]:
            add(f'<path d="{path_d(p)}" fill="{C["path"]}"/>')
        add(f'<path d="{path_d(self.road)}" fill="{C["road"]}"/>')
        add(f'<path d="{path_d(self.parks)}" fill="{C["park"]}"/>')
        pcut0 = unary_union([cc.buffer(rr) for cc, rr, o in self.pcircles]) if self.pcircles else Polygon()
        add(f'<path d="{path_d(self.bufs.difference(pcut0))}" fill="url(#hatch-{clipid})"/>')
        for p, s, e in self.posts:
            add(f'<path d="{path_d(p.difference(pcut0))}" fill="url(#hatch-{clipid})"/>')
        raised = self.raised
        if self.pcircles:
            pc = unary_union([cc.buffer(rr) for cc, rr, o in self.pcircles])
            raised = raised.difference(pc)
        add(f'<path d="{path_d(raised)}" fill="{C["isl"]}"/>')
        if not self.pmeds.is_empty:
            add(f'<path d="{path_d(self.pmeds)}" fill="url(#yhatch-{clipid})"/>')
        for g in self.islands_p:
            add(f'<path d="{path_d(g)}" fill="{C["isl"]}" stroke="{C["walk"]}" stroke-width="0.25"/>')
        for g in self.rings:
            add(f'<path d="{path_d(g)}" fill="{C["bike"]}"/>')
        for f in self.features('island'):
            add(f'<path d="{path_d(f["geom"])}" fill="{C["isl"]}"/>')
        for f in self.features('planted'):
            add(f'<path d="{path_d(f["geom"])}" fill="{C["grass"]}" stroke="{C["isl"]}" stroke-width="0.4"/>')
        # bike facilities
        pcut = unary_union([o.union(cc.buffer(rr)) for cc, rr, o in self.pcircles]) if self.pcircles else Polygon()
        pcut = unary_union([cc.buffer(rr) for cc, rr, o in self.pcircles]) if self.pcircles else Polygon()
        bike_geoms = []
        for p, k, s, e in self.bikes:
            if not pcut.is_empty:
                p = p.difference(pcut)
            if k == 'bl':
                bike_geoms.append(p.difference(self.zone_union))
            else:
                others = [o for o in self.car_by_seg if o[0] is not s]
                bike_geoms.append(p.difference(unary_union([o[1] for o in others])) if others else p)
        for f in self.features('bike'):
            bike_geoms.append(f['geom'])
        add(f'<path d="{path_d(unary_union(bike_geoms))}" fill="{C["bike"]}"/>')
        # flex posts as dots along the middle of each post buffer
        for p, s, e in self.posts:
            ln = offset_line(s['line'], (e['oL'] + e['oR']) / 2)
            if ln is None:
                continue
            ln = ln.difference(self.zone_union.buffer(1.5))
            if self.pcircles:
                ln = ln.difference(unary_union([cc.buffer(rr) for cc, rr, o in self.pcircles]))
            for g in getattr(ln, 'geoms', [ln]):
                n = int(g.length // 3)
                for i in range(n + 1):
                    q = g.interpolate(i * 3 + 1)
                    if self.frame.buffer(2).contains(q):
                        add(f'<circle cx="{fmt(q.x)}" cy="{fmt(q.y)}" r="0.28" fill="{C["white"]}" stroke="{C["road"]}" stroke-width="0.1"/>')
        # two-way left-turn lane markings
        if not self.tws.is_empty:
            add(f'<path d="{path_d(self.tws)}" fill="none" stroke="{C["yellow"]}" stroke-width="0.15"/>')
        # rail lines
        for wid in self.L.get('rail', []):
            g = self.way_line(wid)
            add(f'<path d="{path_d(g)}" fill="none" stroke="{C["rail"]}" stroke-width="2.6" stroke-dasharray="0.25 0.55"/>')
            for o in (0.72, -0.72):
                og = offset_line(g, o)
                if og is not None:
                    add(f'<path d="{path_d(og)}" fill="none" stroke="{C["rail"]}" stroke-width="0.22"/>')
        out += self.markings(clipid)
        out += self.crossings()
        for f in self.features('raised_xing'):
            add(f'<path d="{path_d(f["geom"])}" fill="{C["raised"]}" opacity="0.55"/>')
        out += self.labels()
        add('</g>')
        out += self.callout_marks()
        add(f'<rect x="{-hw}" y="{-hh}" width="{2 * hw}" height="{2 * hh}" fill="none" stroke="var(--rule)" stroke-width="0.4"/>')
        add(self.scalebar(hw, hh))
        add('</svg>')
        return ''.join(out)

    def markings(self, clipid):
        out = []
        W = C['white']
        Y = C['yellow']
        zones = self.zone_union
        for s in self.segs:
            els = [e for e in s['els']]
            if s.get('unmarked'):
                continue
            for i in range(len(els) - 1):
                a, b = els[i], els[i + 1]
                if a['k'] == 'yy' or b['k'] == 'yy':
                    continue
                if a['k'] not in PAVED or b['k'] not in PAVED:
                    continue
                o = a['oR']
                ln = offset_line(s['line'], o)
                if ln is None:
                    continue
                ln = ln.difference(zones).intersection(self.big)
                if ln.is_empty:
                    continue
                d = path_d(ln)
                if a['k'] == 'lane' and b['k'] == 'lane':
                    if a['d'] == b['d']:
                        out.append(f'<path d="{d}" fill="none" stroke="{W}" stroke-width="0.15" stroke-dasharray="3 6"/>')
                    else:
                        for off in (0.12, -0.12):
                            l2 = offset_line(s['line'], o + off)
                            if l2 is not None:
                                out.append(f'<path d="{path_d(l2.difference(zones).intersection(self.big))}" fill="none" stroke="{Y}" stroke-width="0.13"/>')
                elif 'tw' in (a['k'], b['k']):
                    out.append(f'<path d="{d}" fill="none" stroke="{Y}" stroke-width="0.15"/>')
                    inner = o - 0.3 if a['k'] == 'tw' else o + 0.3
                    l2 = offset_line(s['line'], inner)
                    if l2 is not None:
                        out.append(f'<path d="{path_d(l2.difference(zones).intersection(self.big))}" fill="none" stroke="{Y}" stroke-width="0.13" stroke-dasharray="3 6"/>')
                else:
                    out.append(f'<path d="{d}" fill="none" stroke="{W}" stroke-width="0.15"/>')
            # double yellow where marked explicitly
            for i, e in enumerate(els):
                if e['k'] == 'yy':
                    for off in (0.12, -0.12):
                        l2 = offset_line(s['line'], e['oL'] + off)
                        if l2 is not None:
                            out.append(f'<path d="{path_d(l2.difference(zones).intersection(self.big))}" fill="none" stroke="{Y}" stroke-width="0.13"/>')
            # bike symbols in painted/protected bike lanes
            for e in els:
                if e['k'] in ('bl', 'cb'):
                    ln = offset_line(s['line'], (e['oL'] + e['oR']) / 2)
                    if ln is None or ln.length < 20:
                        continue
                    q = ln.interpolate(0.5, normalized=True)
                    if self.frame.contains(q) and not zones.buffer(4).contains(q):
                        out.append(f'<circle cx="{fmt(q.x)}" cy="{fmt(q.y)}" r="0.42" fill="none" stroke="{W}" stroke-width="0.13"/>')
        out += self.stops_and_arrows()
        return out

    def approach_ends(self, s):
        """(junction node, distance from the way start of the junction, sign) for each end of a segment meeting a junction."""
        res = []
        ns = s['nodes']
        line = s['line']
        for n in self.junctions:
            if n in ns:
                p = Point(self.junctions[n])
                t = line.project(p)
                res.append((n, t))
        return res

    def stops_and_arrows(self):
        out = []
        W = C['white']
        stop_at = self.L.get('stop', {})
        for s in self.segs:
            line = s['line']
            for n, t in self.approach_ends(s):
                for direction in (1, -1):
                    # lanes travelling toward the junction: forward lanes if the junction is ahead (t > midpoint)
                    toward = (direction == 1 and t > 1) or (direction == -1 and t < line.length - 1)
                    if not toward:
                        continue
                    lanes = [e for e in s['els'] if e['k'] == 'lane' and e['d'] == direction]
                    if not lanes:
                        continue
                    key = f"{s['wid']}:{n}"
                    zr = self.zones[n].exterior.distance(Point(self.junctions[n])) if n in self.zones else 6
                    # stop bar sits 4 ft behind the outer edge of the nearest crosswalk on this approach
                    dflt = zr + 0.6
                    for xl in self.crossing_lines():
                        hit = xl.intersection(line)
                        if hit.is_empty or hit.geom_type != 'Point':
                            continue
                        dc = abs(t - line.project(hit))
                        if dc < 30 and (t - line.project(hit)) * direction > 0:
                            dflt = max(dflt, dc + 1.5 + 1.2)
                    ds = stop_at.get(self.mode, {}).get(key, stop_at.get(key, dflt))
                    if ds is None:
                        continue
                    ts = t - ds * direction
                    if ts < 0 or ts > line.length:
                        continue
                    a = line.interpolate(max(0, min(line.length, ts - 0.5)))
                    b = line.interpolate(max(0, min(line.length, ts + 0.5)))
                    ang = math.atan2(b.y - a.y, b.x - a.x) if direction == 1 else math.atan2(a.y - b.y, a.x - b.x)
                    oL = max(e['oL'] for e in lanes)
                    oR = min(e['oR'] for e in lanes)
                    p0 = line.interpolate(ts)
                    nx, ny = -math.sin(math.atan2(b.y - a.y, b.x - a.x)), math.cos(math.atan2(b.y - a.y, b.x - a.x))
                    # shapely offsets: + = left, which in SVG (y down) is the (+y,-x) normal of the direction
                    nx, ny = (b.y - a.y), -(b.x - a.x)
                    L = math.hypot(nx, ny) or 1
                    nx, ny = nx / L, ny / L
                    x1, y1 = p0.x + nx * oL, p0.y + ny * oL
                    x2, y2 = p0.x + nx * oR, p0.y + ny * oR
                    if self.frame.buffer(5).contains(Point(x1, y1)):
                        out.append(f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{W}" stroke-width="0.55"/>')
                    # arrows 2.5 m behind the stop bar
                    ta = ts - 2.5 * direction - (4.6 if direction == 1 else -4.6) * 0  # tail position
                    for e in lanes:
                        if not e['turn']:
                            continue
                        oc = (e['oL'] + e['oR']) / 2
                        tail_t = ts - direction * 7.5
                        if tail_t < 0 or tail_t > line.length:
                            continue
                        q = line.interpolate(tail_t)
                        qx, qy = q.x + nx * oc, q.y + ny * oc
                        # travel direction unit vector
                        dx, dy = math.cos(ang), math.sin(ang)
                        # local frame: +y forward, +x driver's right. Driver's right in SVG coords = (-dy, dx)
                        rx, ry = -dy, dx
                        for part in arrow_glyph(e['turn']):
                            pts = [(qx + px * rx + py * dx, qy + px * ry + py * dy) for px, py in part]
                            out.append('<polyline points="' + ' '.join(f'{fmt(u)},{fmt(v)}' for u, v in pts) +
                                       f'" fill="none" stroke="{W}" stroke-width="0.32" stroke-linecap="round" stroke-linejoin="round"/>')
        return out

    def crossing_lines(self):
        if not hasattr(self, '_xl'):
            self._xl = [x['line'] for x in self.crossing_items() if x['style'] != 'bike']
        return self._xl

    def crossings(self):
        out = []
        items = self.crossing_items()
        return self.draw_crossings(items)

    def station(self, wid, node, d):
        """Point and unit direction on a way, d metres from a node, measured away from the node."""
        line = self.way_line(wid)
        t0 = line.project(Point(self.node_xy(node)))
        sgn = 1 if t0 < line.length / 2 else -1
        t = max(0.0, min(line.length, t0 + sgn * d))
        a = line.interpolate(max(0, t - 0.5))
        b = line.interpolate(min(line.length, t + 0.5))
        L = math.hypot(b.x - a.x, b.y - a.y) or 1
        return line, t, ((b.x - a.x) / L, (b.y - a.y) / L), sgn

    def offsets(self, wid, token=None, idx=0):
        els, (cl, cr) = self.layout_xs(wid)
        if token is None:
            return cl, cr
        e = [e for e in els if e['k'] == token]
        if not e:
            return cl, cr
        return e[idx]['oL'], e[idx]['oR']

    def auto_line(self, x):
        line, t, (dx, dy), sgn = self.station(x['way'], x['node'], x['d'])
        q = line.interpolate(t)
        cl, cr = self.offsets(x['way'])
        nx, ny = dy, -dx  # left normal in SVG space
        a, b = cl + 0.4, cr - 0.4
        return LineString([(q.x + nx * a, q.y + ny * a), (q.x + nx * b, q.y + ny * b)])

    def crossing_items_raw(self):
        cfg = self.L.get('crossings', {})
        out = []
        for wid in cfg.get('osm', []):
            if wid in cfg.get('drop', {}).get(self.mode, []):
                continue
            g = self.way_line(wid)
            out.append(dict(line=LineString([g.coords[0], g.coords[-1]]), style='ladder'))
        for x in cfg.get('auto', []):
            if self.mode in x.get('modes', ('now', 'new')) and x['way'] in self.ways_spec and self.xs_for(x['way']) is not None:
                out.append(dict(line=self.auto_line(x), style=x.get('style', 'ladder')))
        return out

    def crossing_items(self):
        cfg = self.L.get('crossings', {})
        items = []
        for wid in cfg.get('osm', []):
            if wid in cfg.get('drop', {}).get(self.mode, []):
                continue
            g = self.way_line(wid)
            items.append(dict(wid=wid, line=extend(LineString([g.coords[0], g.coords[-1]]), 3), style=cfg.get('style', {}).get(wid, 'ladder')))
        for x in cfg.get('auto', []):
            if self.mode in x.get('modes', ('now', 'new')) and x['way'] in self.ways_spec and self.xs_for(x['way']) is not None:
                st = x.get('style', 'ladder')
                if isinstance(st, dict):
                    st = st.get(self.mode, 'ladder')
                items.append(dict(line=self.auto_line(x), style=st))
        for wid in self.L.get('bike_xings', []):
            if self.osm_ways[wid]['tags'].get('crossing:markings') == 'no' and wid not in self.L.get('restyle_bike', {}).get(self.mode, {}):
                continue
            st = self.L.get('restyle_bike', {}).get(self.mode, {}).get(wid, 'bike')
            items.append(dict(wid=wid, line=extend(self.way_line(wid), 1.0), style=st))
        for x in cfg.get('add', []):
            if self.mode in x.get('modes', ('new',)):
                items.append(dict(line=LineString([self.ll(p) for p in x['line']]), style=x.get('style', 'ladder')))
        if getattr(self, 'pcircles', None):
            items = [it for it in items if not any(it['line'].distance(c) < r for c, r, _ in self.pcircles)]
        items += getattr(self, 'extra_xings', [])
        for wid, st in cfg.get('restyle', {}).get(self.mode, {}).items():
            for it in items:
                if it.get('wid') == wid:
                    it['style'] = st
        return items

    def draw_crossings(self, items):
        out = []
        for x in items:
            ln, st = x['line'], x['style']
            if st == 'raisedbike':  # raised crossing that keeps the bikeway level across a side street
                g = ln.buffer(2.6, cap_style='flat').intersection(self.road)
                out.append(f'<path d="{path_d(g)}" fill="{C["raised"]}"/>')
                st = 'bike'
            if st == 'bike':  # green dashed bike crossing
                g = ln.buffer(1.0, cap_style='flat').intersection(self.road)
                out.append(f'<path d="{path_d(g)}" fill="{C["bike"]}" opacity="0.55"/>')
                for o in (1.0, -1.0):
                    l2 = offset_line(ln, o)
                    if l2 is not None:
                        out.append(f'<path d="{path_d(l2.intersection(self.road))}" fill="none" stroke="{C["white"]}" stroke-width="0.3" stroke-dasharray="0.9 0.9"/>')
                continue
            band = ln.buffer(1.5, cap_style='flat')
            if st == 'raised':
                out.append(f'<path d="{path_d(band.intersection(self.road))}" fill="{C["raised"]}"/>')
            n = int(ln.length / 1.2)
            bars = []
            for i in range(n):
                q0 = ln.interpolate(i * 1.2 + 0.3)
                q1 = ln.interpolate(i * 1.2 + 0.9)
                bars.append(LineString([(q0.x, q0.y), (q1.x, q1.y)]).buffer(1.5, cap_style='flat'))
            g = unary_union(bars).intersection(self.road)
            out.append(f'<path d="{path_d(g)}" fill="{C["white"]}"/>')
        return out

    def place_label(self, lab, want):
        for clear_min in (9.0, 5.0, 0.0):
            r = self._place_label(lab, want, clear_min)
            if r is not None:
                return r
        return None

    def _place_label(self, lab, want, clear_min):
        """Slide a street label along its street until the whole label sits inside the frame and
        clear of the junctions; prefer the spot nearest the requested point."""
        line = self.way_line(lab['way'])
        els, _ = self.layout_xs(lab['way'])
        size = lab.get('size', 2.6)
        half_len = len(lab['t']) * size * 0.29 + 0.8
        side = lab.get('side', 1)
        edge = (max(e['oL'] for e in els) if side > 0 else min(e['oR'] for e in els)) if els else 6
        off = edge + side * (size * 0.85)
        hw, hh = self.L.get('half', (45, 45))
        inner = box(-hw + 1.5, -hh + 1.5, hw - 1.5, hh - 1.5)
        best = None
        for i in range(int(line.length)):
            q = line.interpolate(i)
            a = line.interpolate(max(0, i - 2))
            b = line.interpolate(min(line.length, i + 2))
            dx, dy = b.x - a.x, b.y - a.y
            L = math.hypot(dx, dy) or 1
            dx, dy = dx / L, dy / L
            nx, ny = dy, -dx  # real-world left
            cx, cy = q.x + nx * off, q.y + ny * off
            ends = [(cx - dx * half_len + sx * nx * size * 0.5, cy - dy * half_len + sx * ny * size * 0.5) for sx in (-1, 1)] + \
                   [(cx + dx * half_len + sx * nx * size * 0.5, cy + dy * half_len + sx * ny * size * 0.5) for sx in (-1, 1)]
            if not all(inner.contains(Point(e)) for e in ends):
                continue
            clear = min([Point(cx, cy).distance(Point(j)) for j in self.junctions.values()] or [99])
            if clear < clear_min + (half_len * 0.5 if clear_min else 0):
                continue
            body = LineString([(cx - dx * half_len, cy - dy * half_len), (cx + dx * half_len, cy + dy * half_len)]).buffer(size * 0.6)
            if any(body.intersects(o) for o in self._placed):
                continue
            score = math.hypot(cx - want[0], cy - want[1])
            if best is None or score < best[0]:
                ang = math.degrees(math.atan2(dy, dx))
                rot = ang if -90 <= ang <= 90 else ang - 180 if ang > 90 else ang + 180
                best = (score, cx, cy + size * 0.35, rot)
        if best is None:
            return None
        _, cx, cy, rot = best
        r = math.radians(rot)
        self._placed.append(LineString([(cx - math.cos(r) * half_len, cy - math.sin(r) * half_len),
                                        (cx + math.cos(r) * half_len, cy + math.sin(r) * half_len)]).buffer(size * 0.6))
        return best[1:]

    def labels(self):
        out = []
        self._placed = []
        for lab in self.L.get('labels', []):
            if self.mode not in lab.get('modes', ('now', 'new')):
                continue
            x, y = self.ll(lab['at'])
            rot = lab.get('rot', 0)
            if 'way' in lab and lab['way'] in self.osm_ways and self.xs_for(lab['way']) is not None:
                placed = self.place_label(lab, (x, y))
                if placed is None:
                    continue
                x, y, rot = placed
            out.append(f'<text x="{fmt(x)}" y="{fmt(y)}" transform="rotate({rot} {fmt(x)} {fmt(y)})" text-anchor="middle" '
                       f'font-size="{lab.get("size", 2.6)}" font-weight="600" fill="{C["label"]}" stroke="{C["halo"]}" stroke-width="0.7" '
                       f'paint-order="stroke" class="dg-lab">{lab["t"]}</text>')
        return out

    def callout_marks(self):
        out = []
        if self.mode != 'new':
            return out
        for c in self.L.get('callouts', []):
            x, y = c['xy'] if 'xy' in c else self.ll(c['at'])
            if c.get('t') and self.L.get('badges'):
                tw = len(c['t']) * 1.32 + 3.6
                anchor = c.get('side', 1)
                bx = x + 1.2 if anchor > 0 else x - 1.2 - tw
                out.append(f'<g class="dg-badge"><rect x="{fmt(bx)}" y="{fmt(y - 1.9)}" width="{fmt(tw)}" height="3.8" rx="1.9" fill="{C["halo"]}" stroke="{C["call"]}" stroke-width="0.35"/>'
                           f'<text x="{fmt(bx + (tw + 2.2) / 2 if anchor > 0 else bx + (tw - 2.2) / 2)}" y="{fmt(y + 0.85)}" text-anchor="middle" font-size="2.35" font-weight="600" fill="{C["label"]}">{c["t"]}</text></g>')
            out.append(f'<g class="dg-call"><circle cx="{fmt(x)}" cy="{fmt(y)}" r="2.3" fill="{C["call"]}" stroke="{C["halo"]}" stroke-width="0.5"/>'
                       f'<text x="{fmt(x)}" y="{fmt(y + 1.05)}" text-anchor="middle" font-size="3" font-weight="700" fill="{C["halo"]}">{c["n"]}</text></g>')
        return out

    def scalebar(self, hw, hh):
        L = 50 * FT
        x0, y0 = -hw + 3, hh - 3
        return (f'<g class="dg-scale"><rect x="{fmt(x0)}" y="{fmt(y0 - 1.2)}" width="{fmt(L)}" height="1.2" fill="{C["label"]}"/>'
                f'<text x="{fmt(x0 + L + 1.5)}" y="{fmt(y0)}" font-size="2.6" fill="{C["label"]}" stroke="{C["halo"]}" stroke-width="0.6" paint-order="stroke">50 ft</text>'
                f'<g transform="translate({fmt(hw - 4)} {fmt(-hh + 5)})"><path d="M0,-3 L1.4,1.2 L0,0.4 L-1.4,1.2 Z" fill="{C["label"]}"/>'
                f'<text y="4.4" text-anchor="middle" font-size="2.6" fill="{C["label"]}">N</text></g></g>')


def substring(line, s0, s1):
    from shapely.ops import substring as ss
    return ss(line, s0, s1)


def render_site(osm, layout, mode):
    ways = {e['id']: e for e in osm if e['type'] == 'way'}
    nodes = {}
    for e in osm:
        if e['type'] == 'node':
            nodes[e['id']] = e
        elif e['type'] == 'way':
            for nid, g in zip(e['nodes'], e['geometry']):
                nodes.setdefault(nid, dict(lat=g['lat'], lon=g['lon']))
    s = Site(ways, nodes, layout, mode).build()
    return s.render(title=f"{layout['name']}, {'today' if mode == 'now' else 'as proposed'}")
