from bpy.types import Context, Panel

from ..utils.wrappers import Registerable
from .operator import DisplacementBakerOperator
from .properties import DisplacementBakerProperties


class DisplacementBakerPanel(Panel, Registerable):
    """
    Panel for running the Displacement Baker operator.
    """

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
        props = getattr(context.scene, DisplacementBakerProperties.bl_idname)
        col = self.layout.column()
        for propname in DisplacementBakerProperties.get_props():
            col.prop(props, propname)

        self.layout.operator(DisplacementBakerOperator.bl_idname)
