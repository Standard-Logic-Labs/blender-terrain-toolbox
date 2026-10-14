"""Versioned, JSON-safe source data. Grid indices are always global integers."""
import copy
import json
import math

SCHEMA = 1
TILE_SIZE = 512
MAX_CELLS = 400_000  # Deliberate synchronous Python milestone guard.


def default_state():
    return dict(schema=SCHEMA, tile_size=TILE_SIZE, tiles=[[0, 0], [1, 0]],
                preview_spacing=32, final_spacing=16, mode='PREVIEW',
                z_min=-192, z_max=128, seed=17, operations=[],
                guide=True, guide_interval=10, guide_z=0.05, wire=False)


def validate(s):
    if s.get('schema') != SCHEMA or s.get('tile_size') != TILE_SIZE:
        raise ValueError('Unsupported terrain schema or tile size.')
    tiles = s['tiles']
    if not 1 <= len(tiles) <= 8 or len({tuple(t) for t in tiles}) != len(tiles):
        raise ValueError('Use one to eight unique tiles.')
    if any(len(t) != 2 or any(type(v) is not int for v in t) for t in tiles):
        raise ValueError('Tile coordinates must be integer pairs.')
    todo, seen = {tuple(t) for t in tiles}, set()
    frontier = [tuple(tiles[0])]
    while frontier:
        p = frontier.pop()
        if p in seen:
            continue
        seen.add(p)
        frontier.extend(q for q in ((p[0]-1,p[1]), (p[0]+1,p[1]),
                                    (p[0],p[1]-1), (p[0],p[1]+1))
                        if q in todo and q not in seen)
    if seen != todo:
        raise ValueError('Tiles must be edge-connected.')
    for key in ('preview_spacing', 'final_spacing'):
        if s[key] not in (8, 16, 32, 64):
            raise ValueError('Milestone spacing must be 8, 16, 32, or 64 m.')
    if s['mode'] not in ('PREVIEW', 'FINAL'):
        raise ValueError('Invalid build mode.')
    for key in ('z_min', 'z_max', 'guide_z'):
        if not math.isfinite(s[key]):
            raise ValueError('Nonfinite bounds or guide height.')
    if s['z_min'] >= s['z_max']:
        raise ValueError('Vertical minimum must be below maximum.')
    for h in (s['preview_spacing'], s['final_spacing']):
        if s['z_min'] % h or s['z_max'] % h:
            raise ValueError('Vertical bounds must align to BOTH voxel spacings.')
    if s['guide_interval'] not in (5, 10):
        raise ValueError('Guide interval must be 5 or 10 m.')
    if type(s['seed']) is not int:
        raise ValueError('Seed must be an integer.')
    for op in s['operations']:
        if op['kind'] not in ('SPHERE_CUT', 'SPHERE_ADD'):
            raise ValueError('Unknown operation; source left untouched.')
        if len(op['center']) != 3 or not all(math.isfinite(x) for x in op['center']):
            raise ValueError('Invalid sphere center.')
        if not math.isfinite(op['radius']) or op['radius'] <= 0:
            raise ValueError('Sphere radius must be positive.')
    return s


def spacing(s):
    return s['preview_spacing'] if s['mode'] == 'PREVIEW' else s['final_spacing']


def estimate(s):
    validate(s)
    h = spacing(s)
    cells = len(s['tiles']) * (TILE_SIZE // h)**2 * int((s['z_max']-s['z_min'])/h)
    # Six tetrahedra, at most two triangles each. Deliberately conservative
    # planning allowance including Python staging, Blender mesh, and one undo copy.
    return dict(cells=cells, triangle_ceiling=12*cells,
                planning_mib=math.ceil(cells*12*320 / 2**20 + 16))


def dumps(s):
    return json.dumps(validate(s), sort_keys=True, separators=(',', ':'), allow_nan=False)


def loads(text):
    return validate(json.loads(text))


def with_test_cut(s):
    result = copy.deepcopy(s)
    if any(o.get('id') == 'seam-test' for o in result['operations']):
        raise ValueError('Test cut already exists. Toggle it or reset the test terrain.')
    result['operations'].append(dict(id='seam-test', kind='SPHERE_CUT',
                                    center=[512., 256., -32.], radius=96., enabled=True))
    return validate(result)
