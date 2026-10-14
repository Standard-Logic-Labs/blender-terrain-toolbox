"""Blender datablock adapter. Source is saved JSON on Scene, not Python globals."""
import uuid
import bpy
from .core import state
from .core.meshing import extract_tile
from .normals import set_shared_normals

SOURCE_KEY = 'terrain_authoring_source_v1'
OWNER_KEY = 'terrain_authoring_owner'


def read(scene):
    raw = scene.get(SOURCE_KEY)
    return state.loads(raw) if raw else None


def owned(scene, source):
    return [o for o in scene.objects if o.get(OWNER_KEY) == source.get('group_id')]


def require_safe(scene, source):
    if scene.library:
        raise ValueError('Use a local, editable scene.')
    if source:
        for obj in owned(scene, source):
            if obj.library or len(obj.users_scene) > 1 or obj.data.library:
                raise ValueError('Terrain objects are linked/shared across scenes. Use an independent scene.')


def guide_geometry(source, major):
    """Planar reference ribbons, one meter apart; no relationship to voxels.
    Deduplicate identical tile boundary segments. Strong lines are wider.
    """
    verts, faces, segments = [], [], set()
    interval = source['guide_interval']
    z = source['guide_z']
    width = 0.16 if major else 0.045
    for tx,ty in source['tiles']:
        x0,y0 = tx*512,ty*512
        for step in range(513):
            if ((x0+step) % interval == 0) == major:
                segments.add(((x0+step,y0),(x0+step,y0+512)))
            if ((y0+step) % interval == 0) == major:
                segments.add(((x0,y0+step),(x0+512,y0+step)))
    for a,b in sorted(segments):
        dx,dy = (width/2,0) if a[0] == b[0] else (0,width/2)
        offset = len(verts)
        verts.extend(((a[0]-dx,a[1]-dy,z),(a[0]+dx,a[1]+dy,z),
                      (b[0]+dx,b[1]+dy,z),(b[0]-dx,b[1]-dy,z)))
        faces.append(tuple(offset+i for i in range(4)))
    return verts,faces


def rebuild(scene, source):
    """Stage meshes before replacing owned output; leave unrelated objects alone."""
    state.validate(source)
    old_source = read(scene)
    require_safe(scene, old_source)
    estimate = state.estimate(source)
    if estimate['cells'] > state.MAX_CELLS:
        raise ValueError(f"{estimate['cells']:,} cells exceeds the {state.MAX_CELLS:,}-cell milestone limit.")
    source = dict(source)
    source['group_id'] = source.get('group_id') or uuid.uuid4().hex
    # Numeric work completes before any scene mutations.
    tiles = [(tile,extract_tile(source,tile)) for tile in source['tiles']]
    staged_meshes, staged_objects = [], []
    collection = bpy.data.collections.new('Terrain Authoring')
    collection[OWNER_KEY] = source['group_id']
    try:
        def make_object(name, verts, faces, role, normals=None):
            mesh = bpy.data.meshes.new(name)
            staged_meshes.append(mesh)
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            if normals is not None:
                for poly in mesh.polygons:
                    poly.use_smooth = True
                set_shared_normals(mesh, normals, bpy.app.version_string)
            obj = bpy.data.objects.new(name,mesh)
            staged_objects.append(obj)
            obj[OWNER_KEY],obj['terrain_role'] = source['group_id'],role
            collection.objects.link(obj)
            obj.lock_location = (True,)*3
            obj.lock_rotation = (True,)*3
            obj.lock_scale = (True,)*3
            return obj
        for tile,data in tiles:
            obj = make_object(f'Terrain [{tile[0]},{tile[1]}]',data.vertices,data.faces,'TILE',data.normals)
            obj['tile_x'],obj['tile_y'] = tile
            obj.show_wire = source['wire']
            obj.show_all_edges = source['wire']
        for major in (False,True):
            v,f = guide_geometry(source,major)
            obj = make_object('Guide major' if major else 'Guide 1m',v,f,'GUIDE')
            obj.hide_select = True
            obj.hide_render = True
            obj.hide_viewport = not source['guide']
            obj.show_in_front = True
            # Useful in Material Preview; solid viewport also distinguishes width.
            mat = bpy.data.materials.get('Terrain Authoring Guide')
            if mat is None:
                mat = bpy.data.materials.new('Terrain Authoring Guide')
                mat.diffuse_color = (0.16,0.38,0.23,1)
            obj.data.materials.append(mat)
    except Exception:
        for obj in staged_objects:
            bpy.data.objects.remove(obj,do_unlink=True)
        for mesh in staged_meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        bpy.data.collections.remove(collection)
        raise
    previous = owned(scene,old_source) if old_source else []
    old_collections = {c for obj in previous for c in obj.users_collection
                       if c.get(OWNER_KEY) == source['group_id']}
    scene.collection.children.link(collection)
    scene[SOURCE_KEY] = state.dumps(source)
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = 'METERS'
    for obj in previous:
        mesh = obj.data
        bpy.data.objects.remove(obj,do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for old in old_collections:
        if not old.objects and not old.children:
            bpy.data.collections.remove(old)
    for obj in staged_objects:
        if obj['terrain_role'] == 'TILE':
            obj.name = f"Terrain [{obj['tile_x']},{obj['tile_y']}]"
            obj.data.name = obj.name
    return source


def toggle_display(scene, key):
    source = read(scene)
    require_safe(scene,source)
    source[key] = not source[key]
    for obj in owned(scene,source):
        if key == 'guide' and obj['terrain_role'] == 'GUIDE':
            obj.hide_viewport = not source[key]
        if key == 'wire' and obj['terrain_role'] == 'TILE':
            obj.show_wire = source[key]
            obj.show_all_edges = source[key]
    scene[SOURCE_KEY] = state.dumps(source)
