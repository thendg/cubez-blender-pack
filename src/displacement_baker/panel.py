from bpy.types import Context, Panel

from ..utils.wrappers import Registerable
from .operator import DisplacementBakerOperator


class DisplacementBakerPanel(Panel, Registerable):
    bl_label = "Displacement Baker"
    bl_idname = "VIEW3D_PT_displacement_baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CBP"

    @classmethod
    def poll(cls, context: Context):
        if context.view_layer.objects.active.mode == "OBJECT":
            return True

    def draw(self, context: Context):
        props = self.layout.operator(DisplacementBakerOperator.bl_idname)
