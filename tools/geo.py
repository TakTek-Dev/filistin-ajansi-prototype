"""Builds the base-map geometry for the pafta (the West Bank sheet with a Gaza inset).

python -I tools/geo.py   (from the project root)

Sources (research/geo/, not published):
  adm1.geojson, adm2.geojson   geoBoundaries PSE ADM1/ADM2, CC BY 4.0
  ne_10m_lakes / rivers        Natural Earth, public domain
  barrier_ways.json            OpenStreetMap relation 1410327, ODbL
Output: tools/out/geo.json, every path already projected to sheet units (1 unit = 100 m).
"""
import json, math, os
from shapely.geometry import shape, box, LineString, MultiLineString, Polygon, MultiPolygon, Point
from shapely.ops import unary_union, linemerge

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = lambda *p: os.path.join(ROOT, 'research', 'geo', *p)

KX = 111.32 * math.cos(math.radians(31.95))  # km per degree of longitude
KY = 110.6                                     # km per degree of latitude
U = 10                                         # sheet units per km

# West Bank sheet: true position. Gaza sits in an inset at the same scale, lower left.
WB_LON0, WB_LAT0 = 34.86, 32.575
GAZA_SHIFT_KM = 38.0                           # room on the left for the inset and the legend
GZ_LON0, GZ_LAT0 = 34.195, 31.605
GZ_ORIGIN = (2.0, 95.0)                        # km, top-left of the Gaza drawing inside the sheet
SHEET_W = round(GAZA_SHIFT_KM + (35.595 - WB_LON0) * KX, 1)
SHEET_H = round((WB_LAT0 - 31.335) * KY, 1)

def wb_xy(lon, lat):
    return ((lon - WB_LON0) * KX + GAZA_SHIFT_KM) * U, (WB_LAT0 - lat) * KY * U

def gz_xy(lon, lat):
    return ((lon - GZ_LON0) * KX + GZ_ORIGIN[0]) * U, ((GZ_LAT0 - lat) * KY + GZ_ORIGIN[1]) * U

def rings(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom.exterior.coords] + [r.coords for r in geom.interiors]
    if isinstance(geom, (MultiPolygon,)) or hasattr(geom, 'geoms'):
        out = []
        for g in geom.geoms:
            out += rings(g) if isinstance(g, (Polygon, MultiPolygon)) else []
        return out
    return []

def lines(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, LineString):
        return [geom.coords]
    if hasattr(geom, 'geoms'):
        out = []
        for g in geom.geoms:
            out += lines(g)
        return out
    return []

def path(seqs, proj, close):
    parts = []
    for seq in seqs:
        pts = [proj(x, y) for x, y in seq]
        if len(pts) < 2:
            continue
        q = []
        for x, y in pts:                      # integer units (100 m) are below a pixel at display size
            r = (round(x), round(y))
            if not q or q[-1] != r:
                q.append(r)
        if len(q) < 2:
            continue
        d = 'M' + 'L'.join(f'{x} {y}' for x, y in q)
        parts.append(d + ('Z' if close else ''))
    return ''.join(parts)

def load(name):
    return json.load(open(G(name), encoding='utf-8'))

TOL = 0.0011  # degrees, about 110 m: under one pixel at the sheet's display size

adm1 = {f['properties']['shapeName']: shape(f['geometry']) for f in load('adm1.geojson')['features']}
wb, gz = adm1['West Bank'], adm1['Gaza']

GOV_TR = {
    'Jenin': ('cenin', 'Cenin'), 'Tubas': ('tubas', 'Tubas'), 'Tulkarm': ('tulkerem', 'Tulkerem'),
    'Nablus': ('nablus', 'Nablus'), 'Qalqiliya': ('kalkilya', 'Kalkilya'), 'Salfit': ('selfit', 'Selfit'),
    'Ramallah & Al Bireh': ('ramallah', 'Ramallah ve El Bire'), 'Jericho & Al Aghwar': ('eriha', 'Eriha'),
    'Jerusalem': ('kudus', 'Kudüs'), 'Bethlehem': ('beytullahim', 'Beytüllahim'), 'Hebron': ('el-halil', 'El Halil'),
    'North Gaza': ('kuzey-gazze', 'Kuzey Gazze'), 'Gaza': ('gazze', 'Gazze'), 'Deir Al Balah': ('deyr-el-belah', 'Deyr el-Belah'),
    'Khan Yunis': ('han-yunus', 'Han Yunus'), 'Rafah': ('refah', 'Refah'),
}
govs = []
for f in load('adm2.geojson')['features']:
    g = shape(f['geometry']).buffer(0)
    gid, name = GOV_TR[f['properties']['shapeName']]
    in_gaza = g.representative_point().within(gz.buffer(0.01))
    proj = gz_xy if in_gaza else wb_xy
    simple = g.simplify(0.0022, preserve_topology=True)   # governorate lines are thin dashes: coarser is enough
    c = g.representative_point()
    cx, cy = proj(c.x, c.y)
    b = g.bounds
    lo = g.simplify(0.006, preserve_topology=True)
    govs.append({'id': gid, 'name': name, 'gaza': bool(in_gaza), 'd': path(rings(simple), proj, True), 'lo': path(rings(lo), proj, True),
                 'c': [round(cx, 1), round(cy, 1)], 'lat': [round(b[1], 3), round(b[3], 3)]})

# water
lakes = [shape(f['geometry']) for f in load('ne_10m_lakes.geojson')['features'] if f['properties'].get('name') == 'Dead Sea']
dead_sea = unary_union(lakes)
sheet_box_deg = box(WB_LON0 + (-GAZA_SHIFT_KM) / KX, 31.30, 35.62, 32.60)
dead_sea_c = dead_sea.intersection(box(35.30, 31.30, 35.62, 31.80))
jordan = unary_union([shape(f['geometry']) for f in load('ne_10m_rivers_lake_centerlines.geojson')['features']
                      if f['properties'].get('name') == 'Jordan'])
jordan_c = jordan.intersection(box(35.40, 31.76, 35.62, 32.60))

# the Green Line: the West Bank's edge where it is not the river or the Dead Sea shore
edge = wb.boundary
east = unary_union([jordan.buffer(0.02), dead_sea.buffer(0.02), box(35.47, 31.30, 35.62, 32.60)])
green = edge.difference(east).simplify(TOL)
river_edge = edge.intersection(east).simplify(TOL)

# land outside the two territories, inside the sheet frame (drawn as a dot screen)
frame_wb = box(WB_LON0, 31.335, 35.595, WB_LAT0)
outside = frame_wb.difference(wb.buffer(0)).difference(dead_sea).simplify(TOL)

# Gaza inset: sea to the west of the strip inside the inset frame
gz_frame = box(GZ_LON0, 31.205, 34.585, GZ_LAT0)
land_near = unary_union([shape(f['geometry']) for f in load('ne_10m_land.geojson')['features']
                         if shape(f['geometry']).intersects(gz_frame)]).intersection(gz_frame)
gz_sea = gz_frame.difference(land_near).difference(gz.buffer(0.002)).simplify(TOL)
gz_outside_land = land_near.difference(gz.buffer(0)).simplify(TOL)
gx0, gy0 = gz_xy(GZ_LON0, GZ_LAT0)
gx1, gy1 = gz_xy(34.585, 31.205)

# barrier (OSM); built stretches solid, proposed or under construction dashed
barrier_built, barrier_planned = [], []
bpath = G('barrier_ways.json')
if os.path.exists(bpath):
    for w in json.load(open(bpath, encoding='utf-8')):
        pts = [(p['lon'], p['lat']) for p in w.get('geometry', [])]
        if len(pts) < 2:
            continue
        t = w.get('tags', {})
        planned = t.get('barrier') in ('proposed', 'construction') or 'construction' in t or 'proposed' in t
        (barrier_planned if planned else barrier_built).append(LineString(pts))
def merged(ls):
    if not ls:
        return LineString()
    m = linemerge(unary_union(ls))
    return m.intersection(frame_wb).simplify(TOL * 0.8)

# places (Turkish forms). size: 3 = governorate seat, 2 = town, 1 = camp/village
PLACES = [
    ('Cenin', 32.4607, 35.2961, 3), ('Tubas', 32.3209, 35.3699, 3), ('Tulkerem', 32.3104, 35.0286, 3),
    ('Nablus', 32.2211, 35.2544, 3), ('Kalkilya', 32.1896, 34.9706, 3), ('Selfit', 32.0848, 35.1806, 3),
    ('Ramallah', 31.8996, 35.2042, 3), ('Eriha', 31.8569, 35.4592, 3), ('Kudüs', 31.7767, 35.2345, 3),
    ('Beytüllahim', 31.7054, 35.2024, 3), ('El Halil', 31.5326, 35.0998, 3),
]
GAZA_PLACES = [('Gazze', 31.5017, 34.4668, 3), ('Han Yunus', 31.3462, 34.3060, 2), ('Refah', 31.2969, 34.2455, 2),
               ('Deyr el-Belah', 31.4170, 34.3510, 2)]

def pts(seq, proj):
    out = []
    for n, la, lo, s in seq:
        x, y = proj(lo, la)
        out.append({'name': n, 'x': round(x, 1), 'y': round(y, 1), 'size': s, 'lat': la, 'lon': lo})
    return out

out = {
    'unit': '100 m', 'sheet': {'w': round(SHEET_W * U), 'h': round(SHEET_H * U)},
    'proj': {'kx': KX, 'ky': KY, 'u': U, 'wb': [WB_LON0, WB_LAT0, GAZA_SHIFT_KM], 'gz': [GZ_LON0, GZ_LAT0, *GZ_ORIGIN]},
    'wb': path(rings(wb.simplify(TOL, preserve_topology=True)), wb_xy, True),
    'wbLo': path(rings(wb.simplify(0.006, preserve_topology=True)), wb_xy, True),
    'gz': path(rings(gz.simplify(TOL, preserve_topology=True)), gz_xy, True),
    'govs': govs,
    'green': path(lines(green), wb_xy, False),
    'riverEdge': path(lines(river_edge), wb_xy, False),
    'deadSea': path(rings(dead_sea_c.simplify(TOL)), wb_xy, True),
    'jordan': path(lines(jordan_c.simplify(TOL)), wb_xy, False),
    'outside': path(rings(outside), wb_xy, True),
    'gzFrame': [round(gx0, 1), round(gy0, 1), round(gx1 - gx0, 1), round(gy1 - gy0, 1)],
    'gzSea': path(rings(gz_sea), gz_xy, True),
    'gzLand': path(rings(gz_outside_land), gz_xy, True),
    'barrier': path(lines(merged(barrier_built)), wb_xy, False),
    'barrierPlanned': path(lines(merged(barrier_planned)), wb_xy, False),
    'places': pts(PLACES, wb_xy), 'gazaPlaces': pts(GAZA_PLACES, gz_xy),
}
os.makedirs(os.path.join(ROOT, 'tools', 'out'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'tools', 'out', 'geo.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('sheet', out['sheet'], 'govs', len(govs), 'bytes', sum(len(v) for v in out.values() if isinstance(v, str)))
