from bpy.types import Context, Panel

from ..utils.wrappers import Registerable


class DisplacementBakerPanel(Panel, Registerable):
    bl_label = "Displacement Baker"
    bl_idname = "VIEW3D_PT_displacement_baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cubez Blender Pack"

    def draw(self, context: Context):
        # TODO: call operator
        pass
