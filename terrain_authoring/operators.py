import traceback
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from . import bridge
from .core import state


class TerrainOperator:
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.mode == 'OBJECT'

    def guarded(self, action):
        try:
            action()
            return {'FINISHED'}
        except Exception as exc:
            traceback.print_exc()
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}


class TERRAIN_OT_create(TerrainOperator,bpy.types.Operator):
    bl_idname = 'terrain_authoring.create'
    bl_label = 'Create Two Preview Tiles'
    bl_description = 'Create two 512 m tiles in metric world space; sets scene unit scale to 1'

    def execute(self,context):
        def action():
            if bridge.read(context.scene):
                raise ValueError('Terrain already exists. Use Reset Test Terrain.')
            bridge.rebuild(context.scene,state.default_state())
        return self.guarded(action)


class TERRAIN_OT_cut(TerrainOperator,bpy.types.Operator):
    bl_idname = 'terrain_authoring.test_cut'
    bl_label = 'Add Boundary Test Cut'
    bl_description = 'Subtract a 96 m sphere centered at (512, 256, -32); rebuild both tiles'

    def execute(self,context):
        return self.guarded(lambda: bridge.rebuild(context.scene,state.with_test_cut(bridge.read(context.scene))))


class TERRAIN_OT_toggle_cut(TerrainOperator,bpy.types.Operator):
    bl_idname = 'terrain_authoring.toggle_cut'
    bl_label = 'Enable / Disable Test Cut'

    def execute(self,context):
        def action():
            source = bridge.read(context.scene)
            op = next(o for o in source['operations'] if o.get('id') == 'seam-test')
            op['enabled'] = not op['enabled']
            bridge.rebuild(context.scene,source)
        return self.guarded(action)


class TERRAIN_OT_rebuild(TerrainOperator,bpy.types.Operator):
    bl_idname = 'terrain_authoring.rebuild'
    bl_label = 'Regenerate from Saved Source'

    def execute(self,context):
        return self.guarded(lambda: bridge.rebuild(context.scene,bridge.read(context.scene)))


SPACINGS = [(str(n),f'{n} m','Global voxel spacing') for n in (64,32,16,8)]


class TERRAIN_OT_settings(TerrainOperator,bpy.types.Operator):
    bl_idname = 'terrain_authoring.settings'
    bl_label = 'Build Settings'
    bl_description = 'Stage settings; Apply rebuilds and saves them in one undo step'
    preview_spacing: EnumProperty(name='Preview voxel spacing',items=SPACINGS,default='32')
    final_spacing: EnumProperty(name='Final voxel spacing',items=SPACINGS,default='16')
    mode: EnumProperty(name='Build mode',items=[('PREVIEW','Preview',''),('FINAL','Final','')])
    z_min: IntProperty(name='Minimum Z (m)',default=-192)
    z_max: IntProperty(name='Maximum Z (m)',default=128)
    seed: IntProperty(name='Seed',default=17,min=0,max=65535)
    guide_interval: EnumProperty(name='Major guide interval',items=[('5','5 m',''),('10','10 m','')],default='10')
    guide_z: FloatProperty(name='Guide datum Z (m)',default=0.05)
    accept_cost: BoolProperty(name='I accept this synchronous build cost',default=False,options={'SKIP_SAVE'})

    def source(self,context):
        s = bridge.read(context.scene)
        for key in ('preview_spacing','final_spacing','guide_interval'):
            s[key] = int(getattr(self,key))
        for key in ('mode','z_min','z_max','seed','guide_z'):
            s[key] = getattr(self,key)
        return s

    def invoke(self,context,event):
        s = bridge.read(context.scene)
        for key in ('preview_spacing','final_spacing','guide_interval'):
            setattr(self,key,str(s[key]))
        for key in ('mode','z_min','z_max','seed','guide_z'):
            setattr(self,key,s[key])
        self.accept_cost = False
        return context.window_manager.invoke_props_dialog(self,width=430)

    def draw(self,context):
        layout = self.layout
        for key in ('mode','preview_spacing','final_spacing','z_min','z_max','seed','guide_interval','guide_z'):
            layout.prop(self,key)
        try:
            cost = state.estimate(self.source(context))
            layout.label(text=f"Cells: {cost['cells']:,}; max triangles: {cost['triangle_ceiling']:,}")
            layout.label(text=f"Conservative planning allowance: {cost['planning_mib']:,} MiB")
            layout.label(text='Includes staging and one undo copy; not a RAM guarantee.')
            if cost['cells'] > state.MAX_CELLS:
                layout.label(text='Over milestone cell limit; choose coarser settings.',icon='ERROR')
            if cost['planning_mib'] > 512:
                layout.prop(self,'accept_cost')
        except (ValueError,KeyError,TypeError) as exc:
            layout.label(text=str(exc),icon='ERROR')

    def execute(self,context):
        def action():
            s = self.source(context)
            if state.estimate(s)['planning_mib'] > 512 and not self.accept_cost:
                raise ValueError('Review Build Settings and acknowledge the estimated cost.')
            bridge.rebuild(context.scene,s)
        return self.guarded(action)


class TERRAIN_OT_display(TerrainOperator,bpy.types.Operator):
    bl_idname = 'terrain_authoring.display'
    bl_label = 'Toggle Terrain Display'
    kind: EnumProperty(items=[('guide','1 m guide',''),('wire','Mesh wireframe','')])

    def execute(self,context):
        return self.guarded(lambda: bridge.toggle_display(context.scene,self.kind))


class TERRAIN_OT_reset(TerrainOperator,bpy.types.Operator):
    bl_idname = 'terrain_authoring.reset'
    bl_label = 'Reset Test Terrain'
    bl_description = 'Reset only this terrain group to two default tiles; unrelated scene objects are preserved'

    def invoke(self,context,event):
        return context.window_manager.invoke_confirm(self,event)

    def execute(self,context):
        def action():
            old = bridge.read(context.scene)
            s = state.default_state()
            if old:
                s['group_id'] = old['group_id']
            bridge.rebuild(context.scene,s)
        return self.guarded(action)


class TERRAIN_OT_frame(bpy.types.Operator):
    bl_idname = 'terrain_authoring.frame'
    bl_label = 'Frame Terrain'
    bl_description = 'Select generated tiles and frame them in this viewport'

    @classmethod
    def poll(cls,context):
        return context.area is not None and context.area.type == 'VIEW_3D' and context.mode == 'OBJECT'

    def execute(self,context):
        source = bridge.read(context.scene)
        if not source:
            return {'CANCELLED'}
        for obj in context.selected_objects:
            obj.select_set(False)
        for obj in bridge.owned(context.scene,source):
            if obj['terrain_role'] == 'TILE':
                obj.select_set(True)
                context.view_layer.objects.active = obj
        context.space_data.clip_end = max(context.space_data.clip_end,5000)
        # Panel invocation can have a UI region; view_selected needs WINDOW.
        region = next(r for r in context.area.regions if r.type == 'WINDOW')
        with context.temp_override(region=region):
            bpy.ops.view3d.view_selected(use_all_regions=False)
        return {'FINISHED'}


CLASSES = (TERRAIN_OT_create,TERRAIN_OT_cut,TERRAIN_OT_toggle_cut,
           TERRAIN_OT_rebuild,TERRAIN_OT_settings,TERRAIN_OT_display,
           TERRAIN_OT_reset,TERRAIN_OT_frame)
