import bpy

from ..globals import UITab
from ..tools.translate import t
from ..tools import core


from ..ui import register_ui_tab #need this for registering our class to the ui

#Making a class that looks like a blender panel just to use it to cut the code up for tabs
#This is kinda a bad look but at least it makes the UI nice! - @989onan
@register_ui_tab
class Bake_PT_bake_passes(UITab):
    bl_label = t('BakePanel.bakepasses.label')
    bl_enum = "PASSES"
    bl_description = t('BakePanel.bakepasses.desc')
    icon = "TEXTURE"
    
    def poll(cls, context):
        return True
    
    def draw_panel(main_panel: bpy.types.Panel, context: bpy.types.Context, col: bpy.types.UILayout):
        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_diffuse', expand=True)
        if context.scene.bake_pass_diffuse:
            row = col.row(align=True)
            row.separator()
            row.prop(context.scene, 'bake_diffuse_indirect', expand=True)
            if context.scene.bake_diffuse_indirect:
                row = col.row(align=True)
                row.separator()
                row.prop(context.scene, 'bake_diffuse_indirect_opacity', expand=True)
        col.separator()
        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_normal', expand=True)
        col.separator()
        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_smoothness', expand=True)
        col.separator()
        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_ao', expand=True)
        # Check if user has AO shapekeys when AO pass is enabled
        if context.scene.bake_pass_ao:
            has_ao_keys = False
            for obj in core.get_meshes_objects(context):
                if core.has_shapekeys(obj):
                    for key in obj.data.shape_keys.key_blocks:
                        if ('ambient' in key.name.lower() and 'occlusion' in key.name.lower()) or key.name.endswith('_ao'):
                            has_ao_keys = True
                            break
                if has_ao_keys:
                    break
            
            if not has_ao_keys:
                row = col.row(align=True)
                row.separator()
                row.label(text="Warning: No AO shapekeys detected (e.g., 'ambient_occlusion' or ending in '_ao')", icon="ERROR")
                row = col.row(align=True)
                row.separator()
                row.label(text="AO baking will work but won't use any animated AO keys.")
            
            row = col.row(align=True)
            row.separator()
            row.prop(context.scene, 'bake_illuminate_eyes', expand=True)
            if main_panel.multires_obj_names:
                row = col.row(align=True)
                row.separator()
                row.label(text="One or more of your objects are using Multires.", icon="ERROR")
                row = col.row(align=True)
                row.separator()
                row.label(text="This has issues excluding the eyes, try adding")
                row = col.row(align=True)
                row.separator()
                row.label(text="'ambient occlusion' shape keys instead.")

        col.separator()
        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_alpha', expand=True)
        col.separator()
        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_metallic', expand=True)
        col.separator()

        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_emit', expand=True)
        if context.scene.bake_pass_emit:
            row = col.row(align=True)
            row.separator()
            row.prop(context.scene, 'bake_emit_indirect', expand=True)
            if context.scene.bake_emit_indirect:
                row = col.row(align=True)
                row.separator()
                row.prop(context.scene, 'bake_emit_exclude_eyes', expand=True)

        col.separator()
        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_displacement', expand=True)
        col.separator()
        row = col.row(align=True)
        row.prop(context.scene, 'bake_pass_detail', expand=True)

        row = col.row(align=True)