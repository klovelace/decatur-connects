"""Priority intersections: what the crash records show and what each fix addresses.

Crash counts are computed in build_network.py from data/crashes_2019_2023.csv (every crash
within RADIUS_M of the centre point, each crash assigned to its nearest listed intersection).
The "issues" text summarises the police crash reports for the walking and biking crashes at
each site. Each fix names the issue it answers and, where a federal figure exists, the
measured crash reduction for that treatment.
"""

RADIUS_M = 76  # 250 ft: the usual distance for calling a crash "intersection-related"

# Measured effects. FHWA = Federal Highway Administration Proven Safety Countermeasures fact sheets.
EVIDENCE = {
    'lpi': 'Leading pedestrian interval: 13% fewer pedestrian crashes at intersections (FHWA).',
    'refuge': 'Pedestrian refuge island: 56% fewer pedestrian crashes (FHWA).',
    'hivis': 'High-visibility crosswalks: up to 40% fewer pedestrian injury crashes (FHWA).',
    'light': 'Intersection lighting: up to 42% fewer nighttime pedestrian injury crashes (FHWA).',
    'rrfb': 'Flashing crossing beacon (RRFB): up to 47% fewer pedestrian crashes (FHWA).',
    'roundabout': 'Signal converted to roundabout: 78% fewer fatal and injury crashes (FHWA).',
    'diet': '4-to-3 lane road diet: 19-47% fewer total crashes (FHWA-HRT-10-053).',
    'sbl': 'Painted bike lane upgraded to a separated lane with posts: up to 53% fewer bike-vehicle crashes (FHWA).',
    'access': 'Fewer or tighter driveways on urban arterials: 25-31% fewer fatal and injury crashes (FHWA).',
    'yellow': 'Retimed yellow and all-red intervals: 36-50% less red-light running (FHWA).',
    'design': 'No federal crash figure. The design removes the conflict or slows the turn.',
}

# centre: ('Street A', 'Street B') resolved on the street network, or (lat, lon) for multi-leg junctions.
INTERSECTIONS = [
    dict(
        id='X1', name='E College Ave / S Candler St / E Trinity Pl / E Howard Ave',
        centre=(33.77130, -84.29285), routes=['C6', 'C11'],
        context='Four streets and the railroad meet at the Agnes Scott gate. A school crossing guard works here.',
        issues=[
            'Six walking and biking crashes involved a driver turning left who did not yield to someone in the crosswalk or to an oncoming rider.',
            'One driver ran a red light and seriously injured a pedestrian in the crosswalk.',
            'A right-turning driver struck the school crossing guard and left. Two of the walking and biking crashes were hit-and-runs.',
            'More crashes of all kinds than any other site on this list.',
        ],
        fixes=[
            ('Protected-only left-turn arrows on E College Ave and S Candler St', 'Left-turning drivers hitting people in the crosswalk', 'design'),
            ('Leading pedestrian interval and no right turn on red', 'Turning drivers who start with the pedestrian and do not look', 'lpi'),
            ('Protected intersection corners with a bike signal where E Trinity meets E Howard', 'Left turns across oncoming riders, including the 2022 serious injury', 'design'),
            ('Retime yellow and all-red intervals; add signal backplates', 'Red-light running', 'yellow'),
            ('Road diet with protected lanes on E College Ave (GDOT project, extended west)', 'Fewer lanes to cross and slower turns', 'diet'),
        ]),
    dict(
        id='X2', name='Commerce Dr / W Trinity Pl / Swanton Way',
        centre=(33.77405, -84.29890), routes=['G5'],
        context='Two signals about 375 ft apart on the Commerce Dr cycle track built from the 2016 PATH plan, on the west edge of downtown.',
        issues=[
            'At least four pedestrians were hit in the crosswalk by drivers turning left from Swanton Way or W Trinity Pl. Several had the walk signal.',
            'Two of the people hit were using wheelchairs.',
            'A driver leaving a driveway hit a rider in the bike lane on Trinity.',
            'The bike facility is already built here. The signal phasing still lets left turns run at the same time as the walk signal.',
        ],
        fixes=[
            ('Protected-only left turns from Swanton Way and W Trinity Pl, separated in time from the walk signal', 'Left-turning drivers hitting people who have the walk signal', 'design'),
            ('Leading pedestrian interval at both signals', 'Gives walkers and wheelchair users a head start so they are visible', 'lpi'),
            ('Hardened centerlines and turn wedges', 'Slows and squares up left turns', 'design'),
            ('Raised crossing and green conflict markings at the Trinity Pl driveways', 'Drivers pulling out across the bike lane', 'access'),
            ('High-visibility crosswalks and lighting check', 'One serious crash happened after dark', 'hivis'),
        ]),
    dict(
        id='X3', name='E College Ave / Commerce Dr',
        centre=('East College Avenue', 'Commerce Drive'), routes=['C3', 'C6'],
        context='Two state routes cross. No bike facility on either. GDOT has a road diet programmed on E College Ave.',
        issues=[
            'A pedestrian standing on the sidewalk was killed in 2023 when a left-turning driver lost control.',
            'Two riders were hit in the crosswalk by left-turning drivers. They were using the crosswalk because there is no bike lane.',
            'A driver changing lanes cut off a rider on E College Ave.',
            'Three of the five walking and biking crashes happened after dark.',
            'For all vehicles, left-turn and lane-change crashes are common here.',
        ],
        fixes=[
            ('Protected intersection with corner islands as part of the GDOT road diet', 'Slows turning drivers and gives riders a marked, separated crossing', 'diet'),
            ('Protected-only left-turn arrows', 'Left-turn crashes, the most common injury pattern here', 'design'),
            ('Separated bike lanes on both streets (C3, C6)', 'Lane-change conflicts and riders pushed into the crosswalk', 'sbl'),
            ('Upgrade intersection lighting', 'Three of five walking and biking crashes were after dark', 'light'),
            ('Leading pedestrian interval and no right turn on red', 'The right-turn crosswalk crash', 'lpi'),
        ]),
    dict(
        id='X4', name='W Ponce de Leon Ave / W Trinity Pl / Adair St',
        centre=('West Ponce de Leon Avenue', 'West Trinity Place'), routes=['C7', 'C12'],
        context='A skewed intersection where the bike lane ends. Residents ranked it their top bike problem in the Safety Action Plan survey.',
        issues=[
            'A rider in the bike lane was seriously injured by a driver changing lanes where the lane drops.',
            'A rider fell after striking a low reflective dome at the edge of the bike lane at night.',
            'A pedestrian was seriously injured in the Adair St crosswalk by a driver coming around the curve.',
            'A right-turning driver blamed the angle of the intersection and glare for not seeing a pedestrian.',
        ],
        fixes=[
            ('Carry the protected bike lane through the intersection; end the merge', 'Lane-change conflict where the bike lane drops', 'sbl'),
            ('Replace low domes with tall reflective posts or a continuous curb', 'Low markers that riders cannot see at night', 'design'),
            ('Square up the corners with curb extensions', 'Skewed angle that hides pedestrians from turning drivers', 'design'),
            ('Raised crosswalk with flashing beacon at Adair St, where the West Side Connector crosses', 'Drivers not yielding as they come around the curve', 'rrfb'),
            ('Leading pedestrian interval and lighting', 'Turning crashes, one after dark', 'lpi'),
        ]),
    dict(
        id='X5', name='N Candler St / Commerce Dr',
        centre=('North Candler Street', 'Commerce Drive'), routes=['C3'],
        context='Four lanes on a curve, with measured speeds of 36-40 mph. The Safety Action Plan lists it for review.',
        issues=[
            'Four serious-injury crashes in five years, the most of any site on this list.',
            'A wheelchair user crossing Commerce Dr was seriously injured by a driver in the inside lane.',
            'A pedestrian with the walk signal was seriously injured by a left-turning driver.',
            'A rider was seriously injured at night on N Candler St.',
            'Many single-vehicle crashes on the curve, several marked speed-related.',
        ],
        fixes=[
            ('Road diet on Commerce Dr: one through lane each way plus a turn lane', 'A second lane of traffic that hides someone crossing; speeds on the curve', 'diet'),
            ('Pedestrian refuge island on Commerce Dr', 'Long four-lane crossing for slower walkers and wheelchair users', 'refuge'),
            ('Protected intersection for the Commerce Dr bike lanes (C3)', 'No bike facility east of Church St', 'sbl'),
            ('Protected-only left-turn arrow and leading pedestrian interval', 'Left turn into a pedestrian who had the signal', 'lpi'),
            ('Curve warning signs, speed feedback sign and lighting', 'Speed-related crashes on the curve, some after dark', 'light'),
        ]),
    dict(
        id='X6', name='Atlanta Ave / W Howard Ave / W College Ave',
        centre=(33.76703, -84.30503), routes=['C5', 'C12'],
        context='The railroad crossing and the Stone Mountain Trail meet two streets at odd angles. The city approved a concept in 2019 to move the crossing to Adair St.',
        issues=[
            'Two riders on the trail crossing were hit by right-turning drivers. One driver was rolling forward on a red light while looking left.',
            'A rider going straight on W College Ave was hit by an oncoming driver turning left onto Atlanta Ave.',
            'A pedestrian crossed away from any crosswalk, which points to crossings that are not where people need them.',
        ],
        fixes=[
            ('Build the 2019 concept: new Adair St crossing with signals at W College Ave and Olympic Pl', 'Too many movements packed into one skewed junction', 'design'),
            ('No right turn on red and a raised trail crossing', 'Right-turning drivers rolling across the trail', 'design'),
            ('Protected-only left turn from W College Ave', 'Left turn across an oncoming rider', 'design'),
            ('Separated two-way path through the crossing for the West Side Connector and the trail', 'Riders mixed with turning traffic at the tracks', 'sbl'),
        ]),
    dict(
        id='X7', name='S McDonough St / College Ave / Howard Ave',
        centre=('South McDonough Street', 'West College Avenue'), routes=['C4', 'C5', 'C6'],
        context='The main rail crossing between downtown and the south side, beside Decatur High School. The N McDonough cycle track ends here.',
        issues=[
            'A rider crossing S McDonough St on College Ave suffered a head injury when a driver entered the intersection.',
            'A rider on E College Ave was hit from behind by a driver following too closely.',
            'A driver leaving a driveway stopped across the N McDonough bike lane in front of a rider.',
        ],
        fixes=[
            ('Protected intersection with a bike signal phase', 'Riders crossing with no signal time or space of their own', 'design'),
            ('Separated bike lanes on College Ave (C5, C6)', 'Riders sharing a lane with following traffic', 'sbl'),
            ('Raised, marked driveway crossings on N McDonough St', 'Drivers blocking or crossing the cycle track', 'access'),
            ('Separated crossing of the tracks linking to the S McDonough spine (C4)', 'The gap between the north and south bike networks', 'design'),
        ]),
    dict(
        id='X8', name='Church St / E Trinity Pl',
        centre=('Church Street', 'East Trinity Place'), routes=['C11'],
        context='A downtown signal near the Square. The Safety Action Plan proposes banning right turns on red at 12 downtown intersections.',
        issues=[
            'All three pedestrian crashes involved a driver turning left into the crosswalk.',
            'One crash sent two pedestrians to the hospital. Another involved a wheelchair user.',
            'One driver said the windshield pillar blocked the view of the crosswalk during the turn.',
        ],
        fixes=[
            ('Protected-only left-turn arrows, with the walk signal held during the arrow', 'Left turns across an occupied crosswalk', 'design'),
            ('Leading pedestrian interval', 'Puts people in the crosswalk before drivers start to turn', 'lpi'),
            ('Hardened centerline and turn wedge', 'Fast, wide left turns where the pillar hides the crosswalk', 'design'),
            ('High-visibility crosswalks and corner daylighting', 'Pedestrians hidden until the last moment', 'hivis'),
        ]),
    dict(
        id='X9', name='Oakview Rd / Mead Rd',
        centre=('Oakview Road', 'Mead Road'), routes=['C4', 'C12'],
        context='An unsignalized crossing near Oakhurst Village and Oakhurst Elementary, where the West Side Connector meets the Oakview spine.',
        issues=[
            'A pedestrian in the marked crosswalk was seriously injured by a driver who did not yield.',
            'A rider entering the crosswalk from the sidewalk collided with a passing vehicle towing a trailer.',
        ],
        fixes=[
            ('Raised crosswalk with a flashing beacon', 'Drivers not yielding at an unsignalized crosswalk', 'rrfb'),
            ('Curb extensions that shorten the crossing and open sight lines', 'People stepping out from behind parked cars', 'design'),
            ('Protected Oakview Rd bikeway (C4) and Mead Rd greenway (C12)', 'Riders on the sidewalk because the street has no facility', 'sbl'),
        ]),
    dict(
        id='X10', name='Church St / Glenlake Commons Dr',
        centre=('Church Street', 'Glenlake Commons Drive'), routes=[],
        context='A side-street exit across the Church St cycle track, built in 2023.',
        issues=[
            'Two riders on the cycle track were hit in 2023 by drivers turning right out of Glenlake Commons Dr.',
            'Both crashes are the same pattern: a driver looks left for a gap in traffic and pulls across the bikeway.',
        ],
        fixes=[
            ('Raised crossing so the bikeway stays level and drivers climb a ramp', 'Drivers rolling across the bikeway without stopping', 'design'),
            ('Stop bar set back behind the bikeway, with green conflict markings and a "look both ways for bikes" sign', 'Drivers looking only one way', 'design'),
            ('Tighter corner radius and trimmed landscaping', 'Fast exits and blocked sight lines', 'access'),
        ]),
    dict(
        id='X11', name='Scott Blvd / Clairemont Ave',
        centre=('Scott Boulevard', 'Clairemont Avenue'), routes=['C1', 'C9'],
        context='Two state routes cross at the corner of the Westchester Elementary school zone. Scott Blvd is posted at 40 mph.',
        issues=[
            'A pedestrian in the crosswalk was killed in 2022.',
            'A high number of crashes of all kinds, led by rear-end and left-turn crashes.',
            'About one in four crashes happened after dark.',
            'The Safety Action Plan found sidewalks under 4 ft wide and pedestrian signal heads mounted above sight lines.',
        ],
        fixes=[
            ('Roundabout or protected-only left turns, decided in the Scott Blvd RAISE study', 'Left-turn crashes and high-speed through movements', 'roundabout'),
            ('Upgrade lighting on all four corners', 'After-dark crashes, including the fatality', 'light'),
            ('Shared-use path with set-back crossings (C9) and lowered pedestrian signal heads', 'Narrow sidewalks at the curb and signals people cannot see', 'hivis'),
            ('Road diet on Clairemont Ave (C1)', 'Rear-end and lane-change crashes on the Clairemont approaches', 'diet'),
        ]),
    dict(
        id='X12', name='Clairemont Ave / Commerce Dr',
        centre=('Clairemont Avenue', 'Commerce Drive'), routes=['C1', 'C3'],
        context='The junction of three bikeways (Clairemont, Commerce, Church) at the edge of downtown.',
        issues=[
            'A rider in the marked bike lane was hit by a driver turning right across the lane.',
            'A high number of crashes of all kinds, mostly rear-end and same-direction sideswipe crashes.',
        ],
        fixes=[
            ('Protected corners with a bike signal or set-back crossing', 'Right turns across the bike lane', 'design'),
            ('Road diet with protected bike lanes on Clairemont Ave north of Commerce Dr (C1)', 'Lane changing and weaving behind the sideswipe and rear-end crashes', 'diet'),
            ('Pedestrian scramble or leading pedestrian interval, as in the 2026 quick-build', 'Heavy foot traffic crossing turning traffic', 'lpi'),
        ]),
]
