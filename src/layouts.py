"""Lane-level layouts for each priority intersection: today (verified) and proposed.

Cross-section strings are read LEFT to RIGHT relative to the OSM way's drawing direction
(the way's 'forward' direction, in real-world terms), so backward ('<') lanes come first,
curb lane first, and forward ('>') lanes follow, centre lane first. See src/diagrams.py.

'now' layouts were checked against Esri World Imagery, Google satellite imagery and Google
Street View (November 2026). Turn arrows are drawn only where imagery or OSM turn tags
confirm them; lanes with no arrow simply have none shown. Crosswalks come from OSM where it
maps them and were added from imagery where it does not ('auto' entries).

Callout numbers match the order of the fixes for each intersection in src/intersections.py.
Callouts use local metres ('xy': x east, y south of the diagram centre).
"""

SW = 'sw@5'
CT = 'cb<@6 curb@3'        # one-way protected bike lane (backward side) + curb buffer
CTF = 'curb@3 cb>@6'       # same, forward side

LAYOUTS = [
    # ------------------------------------------------------------------ X1
    dict(
        id='X1', name='E College Ave / S Candler St / E Trinity Pl / E Howard Ave',
        center=(33.77139, -84.29275), half=(46, 58),
        ways={
            # E College Ave west arm (drawn east, toward S Candler): 1 lane out, left + through/right in
            1322810419: dict(now=f'{SW} < yy >L >TR {SW}', new=f'sw {CT} < yy >L@10 >TR@11 {CTF} sw'),
            # E College Ave east arm (drawn east, away): 3 lanes in (right, through, left), 2 out
            1322820400: dict(now=f'{SW} <R <T <L yy > > {SW}', new=f'sw {CT} <TR <L@10 yy > {CTF} sw'),
            # S Candler St south of College (drawn south, away): 2 in (through-right, left), 1 out
            1378298804: f'{SW} <TR <L yy > {SW}',
            # S Candler St between the tracks and College (drawn south, toward College): 2 lanes south, 1 north
            1509758596: f'{SW} < yy > > {SW}',
            # couplet north of the tracks: two southbound lanes and one northbound lane with a painted median between
            9182325: '> > sw@6',
            1436934513: dict(now='> > sw@6', new='> > curb@3 cb>@6 sw@6'),
            1509758594: dict(now='>@12 sw@6', new='>@12 curb@3 cb>@6 sw@6'),
            # E Trinity Pl NW of the split (drawn SE): 1 lane out, left + through in
            1436934514: dict(now=f'{SW} < yy >L >T {SW}', new=f'sw {CT} < yy >L >T {CTF} sw'),
            1509758595: dict(now=f'{SW} < yy > > {SW}', new=f'sw {CT} < yy > > {CTF} sw'),
            9167694: dict(now=f'{SW} < yy > > {SW}', new=f'sw {CT} < yy > > {CTF} sw'),
            # E Howard Ave arc to N Candler (drawn NE)
            935641057: dict(now=f'{SW} < yy > {SW}', new=f'sw {CT} < yy > {CTF} sw'),
            1509758597: '>@12',
            9191717: f'{SW} >@12 {SW}',
            9189699: '>@12 pk sw',
            9191715: f'{SW} < yy > {SW}',
        },
        gapfill=[dict(ways=[9182325, 1436934513, 1509758594], r=7)],
        rail=[9260410],
        osm_paths=[dict(ways=[43091408, 43091411], w=3.6)],
        crossings=dict(osm=[935641059, 935641060, 935641069, 935641070, 935641071, 935641076, 1387048513, 1387048514]),
        protected=[dict(at=(33.77107, -84.29262), R=26)],
        features=[
            # hardened centreline for the left turn from E Trinity onto the E Howard arc
            dict(type='island', modes=('new',), way=935641057, node=13801087093, d=(3, 8), token='yy', w=0.8),
            # NB bike lane carried through the split, past the left-turn conflict
            dict(type='bike', modes=('new',), link=[(1509758594, 13801087096, 0, 'cb', 0), (1509758595, 13801087093, 2, 'cb', 0)], w=1.8),
        ],
        callouts=[dict(n=1, xy=(-14, 44), t='Left arrows only', side=-1), dict(n=2, xy=(33, 28), t='LPI · no turn on red', side=-1),
                  dict(n=3, xy=(-30, -29), t='Bike signal', side=1), dict(n=4, xy=(-2, 22), t='Retimed signal', side=-1),
                  dict(n=5, xy=(38, 12), t='Road diet', side=-1)],
        labels=[dict(t='E College Ave', at=(33.77083, -84.29320), way=1322810419, side=-1),
                dict(t='S Candler St', at=(33.77070, -84.29262), way=1378298804, side=-1),
                dict(t='E Trinity Pl', at=(33.77180, -84.29330), way=1436934514, side=1),
                dict(t='E Howard Ave', at=(33.77188, -84.29245), way=935641057, side=1),
                dict(t='E Howard Ave (one-way)', at=(33.77135, -84.29330), way=9191717, side=-1, size=2.2)],
    ),
    # ------------------------------------------------------------------ X2
    dict(
        id='X2', name='Commerce Dr / W Trinity Pl / Swanton Way',
        center=(33.77408, -84.29889), half=(36, 72),
        ways={
            # between the signals: sidewalk-level PATH cycle tracks behind planting strips; parking on the east curb mid-block
            74819495: 'sw cb<@6 grass@4 <R <LT yy > > grass@4 cb>@6 sw',
            1382302789: 'sw cb<@6 grass@4 <@13 yy >L >TR pk grass@4 cb>@6 sw',
            178304234: f'sw {CT} <@11 yy >L >TR {CTF} sw',
            9183807: f'{SW} bl<@5 < yy >L >TR bl>@5 {SW}',
            1442124645: f'sw {CT} < < yy >L >TR {CTF} sw',
            965265794: f'{SW} bl<@5 <TR <L yy > bl>@5 {SW}',
            74819496: f'{SW} bl<@5 <TR <L yy > bl>@5 {SW}',
            69963947: f'{SW} <@12 yy >@12 {SW}',
            74819494: f'{SW} <@12 yy >@12 {SW}',
        },
        crossings=dict(osm=[392139744, 392139745, 392139747, 414497332, 965237731, 965237733, 965237734, 980984017],
                       add=[dict(line=[{'xy': (-7.2, 66.1)}, {'xy': (-9.3, 44.9)}], style='bike', modes=('now', 'new')),
                            dict(line=[{'xy': (8.0, 66.1)}, {'xy': (9.0, 45.7)}], style='bike', modes=('now', 'new')),
                            dict(line=[{'xy': (-11.6, -47.0)}, {'xy': (-10.3, -66.4)}], style='bike', modes=('now', 'new')),
                            dict(line=[{'xy': (10.5, -67.2)}, {'xy': (10.8, -46.9)}], style='bike', modes=('now', 'new'))]),
        features=[
            # hardened centrelines on the Commerce Dr legs that left-turning drivers turn into
            dict(type='island', modes=('new',), way=74819495, node=68260959, d=(3.5, 9), token='yy', w=0.8),
            dict(type='island', modes=('new',), way=9183807, node=68260959, d=(3.5, 9), token='yy', w=0.8),
            dict(type='island', modes=('new',), way=1382302789, node=68180255, d=(3.5, 9), token='yy', w=0.8),
            dict(type='island', modes=('new',), way=178304234, node=68180255, d=(3.5, 9), token='yy', w=0.8),
            # raised crossing of the eastbound... westbound cycle track at the parking-deck driveway on W Trinity Pl
            dict(type='raised_xing', modes=('new',), way=1442124645, node=68260959, d=(24, 29), token='cb', idx=-1),
        ],
        callouts=[dict(n=1, xy=(-22, 44), t='Left arrows only', side=1), dict(n=2, xy=(-22, -50), t='LPI', side=1),
                  dict(n=3, xy=(22, 61), t='Hardened centerline', side=-1), dict(n=4, xy=(27, 40), t='Raised driveway crossing', side=-1),
                  dict(n=5, xy=(22, -40), t='High-visibility crosswalks', side=-1)],
        labels=[dict(t='Commerce Dr', at=(33.77410, -84.29890), way=74819495, side=1),
                dict(t='W Trinity Pl', at=(33.77350, -84.29925), way=74819496, side=-1),
                dict(t='Swanton Way', at=(33.77465, -84.29860), way=69963947, side=1)],
    ),
    # ------------------------------------------------------------------ X3
    dict(
        id='X3', name='E College Ave / Commerce Dr', center=(33.77262, -84.28795), half=(42, 42),
        ways={
            74947370: dict(now=f'{SW} < < yy > > {SW}', new=f'sw {CT} <TR <L yy > {CTF} sw'),
            902543449: dict(now=f'{SW} < < yy > > {SW}', new=f'sw {CT} < yy >L >TR {CTF} sw'),
            9183805: dict(now=f'{SW} < yy > > {SW}', new=f'{SW} < yy >L >TR {SW}'),
            1378252225: dict(now=f'{SW} < < yy > > > {SW}', new=f'sw {CT} <TR <L yy > {CTF} sw'),
        },
        rail=[9260410, 25587555, 9176970],
        crossings=dict(osm=[468844374, 468844375, 468844376]),
        protected=[dict(at=(33.77271, -84.28790), R=24)],
        callouts=[dict(n=1, xy=(-16, -18)), dict(n=2, xy=(-24, 15), t='Left arrows only', side=-1), dict(n=3, xy=(26, -6), t='Protected lanes', side=1),
                  dict(n=4, xy=(16, 22), t='Lighting', side=1), dict(n=5, xy=(-30, -2), t='LPI · no turn on red', side=1)],
        labels=[dict(t='E College Ave', at=(33.77243, -84.28838), way=902543449, side=-1),
                dict(t='Commerce Dr', at=(33.77225, -84.28768), way=9183805, side=-1),
                dict(t='Commerce Dr', at=(33.77305, -84.28805), way=1378252225, side=1)],
    ),
    # ------------------------------------------------------------------ X4
    dict(
        id='X4', name='W Ponce de Leon Ave / W Trinity Pl / Adair St', center=(33.77298, -84.30685), half=(46, 40),
        corner_r={'now': 7.5, 'new': 3.5},
        ways={
            # W Ponce west of the merge (drawn east): bike lanes outside parking today; parking-protected proposed
            85333204: dict(now=f'{SW} pk bl<@5 < yy > bl>@5 pk {SW}', new='sw bl<@5 bfr@3 pk < yy > pk bfr@3 bl>@5 sw'),
            85333205: f'{SW} < yy > {SW}',
            85363040: dict(now=f'{SW} bl<@5 < yy > bl>@5 {SW}', new=f'sw {CT} < yy > {CTF} sw'),
            82905179: f'{SW} <@11 >@11 {SW}',
        },
        crossings=dict(osm=[123365725, 414497307, 414497309, 414497306, 414497322, 1388847826],
                       restyle={'new': {414497306: 'raised'}}),
        features=[
            dict(type='bike', modes=('new',), link=[(85333204, 68168712, 6, 'bl', 0), (85363040, 68168712, 7, 'cb', 0)], w=1.6),
            dict(type='bike', modes=('new',), link=[(85333204, 68168712, 6, 'bl', -1), (85363040, 68168712, 7, 'cb', -1)], w=1.6),
        ],
        callouts=[dict(n=1, xy=(16, 13), t='Protected lane carried through', side=1), dict(n=2, xy=(-6, -12), t='Tall posts, not low domes', side=-1),
                  dict(n=3, xy=(32, -10), t='Tighter corners', side=-1), dict(n=4, xy=(-34, 22), t='Raised crosswalk + beacon', side=1),
                  dict(n=5, xy=(8, -22), t='LPI · lighting', side=1)],
        labels=[dict(t='W Ponce de Leon Ave', at=(33.77290, -84.30745), way=85333204, side=-1),
                dict(t='W Trinity Pl', at=(33.77293, -84.30620), way=85363040, side=-1),
                dict(t='W Ponce de Leon Ave', at=(33.77332, -84.30630), way=85333205, side=1),
                dict(t='Adair St', at=(33.77255, -84.30712), way=82905179, side=1)],
    ),
    # ------------------------------------------------------------------ X5
    dict(
        id='X5', name='N Candler St / Commerce Dr', center=(33.77772, -84.29265), half=(42, 40),
        ways={
            1302020956: dict(now=f'{SW} < < yy > > {SW}', new=f'{SW} bl<@5 post@2 < tw@10 > post@2 bl>@5 {SW}'),
            28323849: f'{SW} <@12 yy >@12 {SW}',
            562711984: 'dw@26', 562711980: 'dw@24',
        },
        crossings=dict(osm=[890464821, 890464822, 890464823]),
        protected=[dict(at=(33.77772, -84.29265), R=22)],
        features=[dict(type='island', modes=('new',), way=1302020956, near=(33.77773, -84.29292), length=9, token='tw', inset=0.35),
                  dict(type='island', modes=('new',), way=1302020956, near=(33.77772, -84.29238), length=9, token='tw', inset=0.35)],
        callouts=[dict(n=1, xy=(-34, -12), t='Road diet', side=1), dict(n=2, xy=(-26, 10), t='Refuge island', side=1),
                  dict(n=3, xy=(22, -16), t='Protected corners', side=1), dict(n=4, xy=(12, 26), t='Left arrow only · LPI', side=1),
                  dict(n=5, xy=(-34, 30), t='Curve signs · lighting', side=1)],
        labels=[dict(t='Commerce Dr', at=(33.77762, -84.29320), way=1302020956, side=-1),
                dict(t='N Candler St', at=(33.77735, -84.29262), way=28323849, side=1),
                dict(t='store driveway', at=(33.77805, -84.29267), way=562711984, side=1, size=2.2)],
    ),
    # ------------------------------------------------------------------ X6
    dict(
        id='X6', name='Atlanta Ave / W Howard Ave / W College Ave', center=(33.76700, -84.30520), half=(52, 52),
        ways={
            1530544657: f'{SW} < yy >L >TR {SW}',
            1381105611: f'{SW} <TR <L yy > {SW}',
            1381105610: f'{SW} < yy > {SW}',
            1416945188: f'{SW} < yy > {SW}',
            1443869190: f'{SW} < yy > {SW}',
            9166340: f'{SW} < yy > {SW}',
            # Atlanta Ave across the tracks: replaced by the Adair St crossing in the 2019 concept
            82905180: dict(now=f'{SW} < yy > > {SW}', new=None),
            1423831667: f'{SW} < yy >L >T {SW}',
            1330702381: f'{SW} < yy > {SW}',
            1423831668: f'{SW} <T <L yy >L >T {SW}',
            82905177: f'{SW} < yy > {SW}',
            1416945187: f'{SW} < yy > {SW}',
            1416945186: f'{SW} >@14 {SW}',
            9174248: f'{SW} >@12 {SW}',
            9173861: f'{SW} <@11 >@11 {SW}',
        },
        add_ways=[dict(id='adair_xing', nodes=[13020781804, 68264848], modes=('new',),
                       spec=f'sw ct2@10 curb@3 < yy > {SW}')],
        rail=[9260410],
        osm_paths=[dict(ways=[123367987, 123367996, 126355370, 1387054830], w=3.6)],
        crossings=dict(osm=[126355369, 1353532820, 1387051370, 1387051371, 1387054828, 1387070160],
                       restyle={'new': {1387051370: 'raised'}}),
        bike_xings=[1387054831],
        callouts=[dict(n=1, xy=(-32, 18), t='New Adair St crossing', side=1), dict(n=2, xy=(30, -46), t='No turn on red · raised trail crossing', side=-1),
                  dict(n=3, xy=(30, 22), t='Left arrow only', side=-1), dict(n=4, xy=(-44, -2), t='Two-way path', side=1)],
        labels=[dict(t='W Howard Ave', at=(33.76745, -84.30560), way=1381105611, side=-1),
                dict(t='W College Ave', at=(33.76640, -84.30470), way=1423831667, side=-1),
                dict(t='Atlanta Ave', at=(33.76712, -84.30490), way=9166340, side=-1),
                dict(t='Adair St', at=(33.76695, -84.30570), way=1416945187, side=1)],
    ),
    # ------------------------------------------------------------------ X7
    dict(
        id='X7', name='S McDonough St / College Ave / Howard Ave', center=(33.76985, -84.29655), half=(44, 46),
        ways={
            9174214: dict(now=f'{SW} < yy > > {SW}', new=f'sw {CT} < yy >L >TR {CTF} sw'),
            9182424: dict(now=f'{SW} <T <L yy > {SW}', new=f'sw {CT} <TR <L yy > {CTF} sw'),
            # PATH #2: two-way track on the west side north of College, east side (toward Agnes Scott) south of it
            74927685: dict(now=f'{SW} < yy > {SW}', new=f'sw ct2@10 curb@3 < yy > {SW}'),
            9188301: dict(now=f'{SW} < yy > > {SW}', new=f'{SW} < yy > > curb@3 ct2@10 sw'),
            9190485: f'{SW} < yy > > {SW}',
            84395983: f'{SW} < yy > {SW}',
            630069542: f'{SW} < yy > {SW}',
            9191717: f'{SW} >@12 {SW}',
        },
        rail=[9260410],
        osm_paths=[dict(ways=[43091411, 123381315], w=3.6), dict(ways=[1321963448], w=3.0, bike=True)],
        crossings=dict(osm=[123721496, 1387044434, 1387044435, 123794223, 123794232]),
        bike_xings=[123721489, 123794234, 1388317526],
        protected=[dict(at=(33.76972, -84.29653), R=24)],
        callouts=[dict(n=1, xy=(-14, 26), t='Bike signal phase', side=-1), dict(n=2, xy=(28, 8), t='Protected lanes', side=-1),
                  dict(n=3, xy=(10, -38), t='Raised driveway crossings', side=1), dict(n=4, xy=(-12, -4), t='Two-way track over the tracks', side=-1)],
        labels=[dict(t='W College Ave', at=(33.76950, -84.29710), way=9174214, side=-1),
                dict(t='E College Ave', at=(33.76990, -84.29600), way=9182424, side=1),
                dict(t='S McDonough St', at=(33.76940, -84.29645), way=74927685, side=-1),
                dict(t='W Howard Ave', at=(33.77015, -84.29700), way=630069542, side=1),
                dict(t='N McDonough St', at=(33.77020, -84.29652), way=84395983, side=-1)],
    ),
    # ------------------------------------------------------------------ X8
    dict(
        id='X8', name='Church St / E Trinity Pl', center=(33.77276, -84.29492), half=(40, 40),
        ways={
            9167694: f'{SW} <@12 yy > > {SW}',
            9174771: f'{SW} < yy >L >TR pk {SW}',
            9171846: f'{SW} <@12 yy >@14 {SW}',
            44227138: f'{SW} <@11 yy >@11 {SW}',
            124299298: '>@14',
        },
        crossings=dict(osm=[124299297, 1388817366],
                       auto=[dict(way=9174771, node=68185667, d=12), dict(way=9167694, node=68185667, d=12),
                             dict(way=9171846, node=68185667, d=11)]),
        # hardened centrelines on the legs that left-turning drivers turn into
        features=[dict(type='island', modes=('new',), way=44227138, node=68185667, d=(3.5, 9), token='yy', w=0.8),
                  dict(type='island', modes=('new',), way=9171846, node=68185667, d=(3.5, 9), token='yy', w=0.8)],
        callouts=[dict(n=1, xy=(-30, 6), t='Left arrows only, walk held', side=1), dict(n=2, xy=(18, -28), t='LPI', side=1),
                  dict(n=3, xy=(14, 20), t='Hardened centerline', side=1), dict(n=4, xy=(-30, -24), t='Daylighted corners', side=1)],
        labels=[dict(t='Church St', at=(33.77320, -84.29492), way=44227138, side=1),
                dict(t='E Trinity Pl', at=(33.77245, -84.29445), way=9167694, side=-1),
                dict(t='Trinity Pl', at=(33.77300, -84.29545), way=9174771, side=1)],
    ),
    # ------------------------------------------------------------------ X9
    dict(
        id='X9', name='Oakview Rd / Mead Rd', center=(33.76010, -84.30318), half=(38, 38),
        corner_r={'now': 7.5, 'new': 4.0},
        ways={
            # two-way track on the west side so it meets the Mead Rd greenway without crossing Oakview
            9186478: dict(now=f'{SW} <@11 yy >@11 {SW}', new=f'{SW} <@10 yy >@10 curb@3 ct2@10 sw'),
            1263634144: f'unmarked {SW} <@11 >@11 {SW}',
            74819492: f'{SW} <@11 yy >@11 {SW}',
        },
        crossings=dict(osm=[751198435, 751198436], restyle={'new': {751198436: 'raised'}}),
        callouts=[dict(n=1, xy=(16, -16), t='Raised crosswalk + beacon', side=1), dict(n=2, xy=(-22, 10), t='Tighter corners', side=1),
                  dict(n=3, xy=(-28, -14), t='Mead Rd greenway', side=1)],
        labels=[dict(t='Oakview Rd', at=(33.75985, -84.30335), way=9186478, side=-1),
                dict(t='Mead Rd', at=(33.76020, -84.30360), way=1263634144, side=1)],
    ),
    # ------------------------------------------------------------------ X10
    dict(
        id='X10', name='Church St / Glenlake Commons Dr', center=(33.78581, -84.29159), half=(34, 30),
        corner_r={'now': 7.5, 'new': 4.0},
        ways={
            86529633: 'sw@6 cb<@6 curb@5 <@11 yy >@11 curb@5 cb>@6 sw@6',
            9189159: f'unmarked {SW} <@12 >@12 {SW}',
        },
        bike_xings=[1321936297],
        restyle_bike={'new': {1321936297: 'raisedbike'}},
        stop={'new': {'9189159:68231828': 12.0}},
        callouts=[dict(n=1, xy=(-14, 12), t='Raised bikeway crossing', side=-1), dict(n=2, xy=(14, 20), t='Set-back stop · look both ways', side=-1),
                  dict(n=3, xy=(18, 4), t='Tighter corner', side=1)],
        labels=[dict(t='Church St', at=(33.78605, -84.29180), way=86529633, side=1),
                dict(t='Glenlake Commons Dr', at=(33.78545, -84.29130), way=9189159, side=1)],
    ),
    # ------------------------------------------------------------------ X11
    dict(
        id='X11', name='Scott Blvd / Clairemont Ave', center=(33.78488, -84.30399), half=(42, 42),
        ways={
            46418008: dict(now=f'{SW} <TR <T <L@10 yy > > {SW}', new='path@12 grass@4 <TR <T <L@10 yy > > grass@4 path@12'),
            1322068816: dict(now=f'{SW} < < yy >L@10 >T >TR {SW}', new='path@12 grass@4 < < yy >L@10 >T >TR grass@4 path@12'),
            1320630383: dict(now=f'{SW} <TR <T <L@10 yy > > {SW}', new=f'sw {CT} <TR <L@10 yy > {CTF} sw'),
            1377715235: dict(now=f'{SW} < < yy >L@10 >T >TR {SW}', new=f'sw {CT} < yy >L@10 >TR {CTF} sw'),
            51344341: dict(now=f'{SW} < < yy > > {SW}', new='path@12 grass@4 < < med@8 > > grass@4 path@12'),
            757092026: dict(now=f'{SW} < < yy > > {SW}', new='path@12 grass@4 < < med@8 > > grass@4 path@12'),
            1565898178: dict(now=f'{SW} < < yy > > {SW}', new='path@12 grass@4 < < med@8 > > grass@4 path@12'),
            30977813: dict(now=f'{SW} < < yy > > {SW}', new=f'sw {CT} < tw > {CTF} sw'),
            564285839: dict(now=f'{SW} < < yy > > {SW}', new=f'sw {CT} < tw > {CTF} sw'),
        },
        crossings=dict(osm=[123254542, 123463624, 123806097, 123806099]),
        protected=[dict(at=(33.78488, -84.30399), R=30)],
        callouts=[dict(n=1, xy=(0, 0)), dict(n=2, xy=(-22, -30), t='Lighting, all corners', side=1),
                  dict(n=3, xy=(-30, 26), t='Shared-use path', side=1), dict(n=4, xy=(22, 30), t='Clairemont road diet', side=-1)],
        labels=[dict(t='Scott Blvd', at=(33.78460, -84.30430), way=1322068816, side=1),
                dict(t='Clairemont Ave', at=(33.78515, -84.30430), way=1320630383, side=1)],
    ),
    # ------------------------------------------------------------------ X12
    dict(
        id='X12', name='Clairemont Ave / Commerce Dr', center=(33.77789, -84.29646), half=(42, 42),
        ways={
            30678703: dict(now='sw@6 <R <T <L <L yy > sw@6', new='sw@6 bl<@5 post@2 <TR@10 <L@10 <L@10 yy >@11 post@2 bl>@5 sw@6'),
            1302244828: dict(now='sw@6 < < < yy > sw@6', new='sw@6 bl<@5 post@2 < < yy > post@2 bl>@5 sw@6'),
            1384544864: dict(now='sw@6 < < yy > > sw@6', new='sw@6 bl<@5 post@2 < tw > post@2 bl>@5 sw@6'),
            1560604320: 'sw@6 < yy >L >TR sw@6',
            44227140: f'sw {CT} < < yy >L >T >TR {CTF} sw',
            1302448804: f'sw {CT} <T <L yy > > {CTF} sw',
            1432512849: f'sw {CT} < < yy >L >T >TR {CTF} sw',
            1303021328: f'sw {CT} < < yy > > > {CTF} sw',
            1432512850: f'sw {CT} < < yy > > {CTF} sw',
        },
        crossings=dict(osm=[123461979, 123461985, 123462594, 123718178]),
        bike_xings=[1321875385, 1360731424],
        protected=[dict(at=(33.77789, -84.29646), R=28)],
        callouts=[dict(n=1, xy=(20, -20), t='Bike signal · protected corners', side=-1), dict(n=2, xy=(16, -36), t='Clairemont road diet', side=1),
                  dict(n=3, xy=(-22, 22), t='Scramble or LPI', side=1)],
        labels=[dict(t='Commerce Dr', at=(33.77779, -84.29705), way=1302448804, side=1),
                dict(t='Clairemont Ave', at=(33.77830, -84.29646), way=30678703, side=-1)],
    ),
]
