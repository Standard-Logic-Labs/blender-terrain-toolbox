"""Run only via run_blender_tests.py in an isolated background Blender process."""
import hashlib
import json
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import terrain_authoring
from terrain_authoring import bridge

args = sys.argv[sys.argv.index('--')+1:]
phase, output = args[0],Path(args[1])
terrain_authoring.register()
print('INTEGRATION BLENDER VERSION:',bpy.app.version_string)


def signature(scene):
    s = bridge.read(scene)
    data = []
    for o in sorted(bridge.owned(scene,s),key=lambda o:o.name):
        if o['terrain_role'] != 'TILE':
            continue
        data.append((o['tile_x'],o['tile_y'],
                     [tuple(v.co) for v in o.data.vertices],
                     [tuple(p.vertices) for p in o.data.polygons]))
    return hashlib.sha256(json.dumps(data).encode()).hexdigest()


def check_scene(scene):
    s = bridge.read(scene)
    tiles = sorted((o for o in bridge.owned(scene,s) if o['terrain_role']=='TILE'),key=lambda o:o['tile_x'])
    assert len(tiles) == 2
    assert scene.unit_settings.system == 'METRIC'
    assert scene.unit_settings.scale_length == 1
    borders = []
    normals = []
    for o in tiles:
        assert o.data.has_custom_normals
        assert o.matrix_world.is_identity
        vertices = {v.index:tuple(v.co) for v in o.data.vertices if v.co.x == 512}
        borders.append(set(vertices.values()))
        nmap = {}
        for loop in o.data.loops:
            if loop.vertex_index in vertices:
                nmap.setdefault(vertices[loop.vertex_index],[]).append(tuple(o.data.corner_normals[loop.index].vector))
        normals.append(nmap)
        assert abs(o.dimensions.x-512) < 0.001
        assert abs(o.dimensions.y-512) < 0.001
    assert borders[0] and borders[0] == borders[1]
    for p in borders[0]:
        # Blender stores/quantizes normals; allow 0.002 component error.
        a = normals[0][p][0]
        for b in normals[0][p]+normals[1][p]:
            assert max(abs(x-y) for x,y in zip(a,b)) < 0.002
    assert len([o for o in bridge.owned(scene,s) if o['terrain_role']=='GUIDE']) == 2


if phase == 'create':
    # The runner supplies --factory-startup. Do not delete unrelated scene data.
    assert bpy.ops.terrain_authoring.create() == {'FINISHED'}
    before = signature(bpy.context.scene)
    assert bpy.ops.terrain_authoring.test_cut() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert signature(bpy.context.scene) != before
    check_scene(bpy.context.scene)
    expected = signature(bpy.context.scene)
    assert bpy.ops.terrain_authoring.rebuild() == {'FINISHED'}
    assert signature(bpy.context.scene) == expected
    # Registration cycle preserves source and does not accumulate classes.
    raw = bpy.context.scene[bridge.SOURCE_KEY]
    terrain_authoring.unregister()
    terrain_authoring.register()
    assert bpy.context.scene[bridge.SOURCE_KEY] == raw
    (output/'expected.json').write_text(json.dumps(dict(signature=expected,source=raw)))
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'terrain_roundtrip.blend'))
else:
    bpy.ops.wm.open_mainfile(filepath=str(output/'terrain_roundtrip.blend'))
    expected = json.loads((output/'expected.json').read_text())
    assert bpy.context.scene[bridge.SOURCE_KEY] == expected['source']
    check_scene(bpy.context.scene)
    assert signature(bpy.context.scene) == expected['signature']
    assert bpy.ops.terrain_authoring.rebuild() == {'FINISHED'}
    bpy.context.view_layer.update()
    assert signature(bpy.context.scene) == expected['signature']
    check_scene(bpy.context.scene)
print('PASS:',phase)
