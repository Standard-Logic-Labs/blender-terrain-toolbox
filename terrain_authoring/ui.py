import bpy
from . import bridge
from .core import state


class TERRAIN_PT_main(bpy.types.Panel):
    bl_label = 'Volumetric Terrain · Milestone 1'
    bl_idname = 'TERRAIN_PT_main'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Terrain'

    def draw(self,context):
        layout = self.layout
        layout.label(text=f'Blender {bpy.app.version_string}')
        try:
            s = bridge.read(context.scene)
        except Exception as exc:
            layout.label(text='Source cannot be read; see console.',icon='ERROR')
            layout.label(text=str(exc))
            return
        if not s:
            layout.label(text='Two 512 × 512 m tiles · 32 m preview')
            layout.label(text='Sets metric units: 1 Blender unit = 1 m')
            layout.operator('terrain_authoring.create')
            return
        layout.label(text=f"{len(s['tiles'])} tiles · {state.spacing(s)} m voxels · {s['mode'].lower()}")
        layout.label(text=f"Vertical bounds: {s['z_min']} to {s['z_max']} m")
        layout.operator('terrain_authoring.frame')
        layout.operator('terrain_authoring.settings')
        layout.operator('terrain_authoring.rebuild')
        box = layout.box()
        box.label(text='Ordered operations')
        box.label(text=f"0. Procedural base · seed {s['seed']}")
        cut = next((o for o in s['operations'] if o.get('id') == 'seam-test'),None)
        if cut:
            box.label(text='1. Sphere cut · '+('enabled' if cut['enabled'] else 'disabled'))
            box.operator('terrain_authoring.toggle_cut')
        else:
            box.operator('terrain_authoring.test_cut')
        layout.operator('terrain_authoring.display',text='1 m Guide',depress=s['guide']).kind = 'guide'
        layout.label(text=f"Planar datum at Z {s['guide_z']:.2f} m; major {s['guide_interval']} m")
        layout.operator('terrain_authoring.display',text='Mesh Wireframe',depress=s['wire']).kind = 'wire'
        layout.separator()
        layout.operator('terrain_authoring.reset')
        layout.label(text='Development reload: dev/reload_addon.py')


CLASSES = (TERRAIN_PT_main,)
