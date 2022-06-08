from bpy.types import Context, Panel

import utils
from ..utils.wrappers import Registerable
from .operator import MMOperator
from .properties import MMProperties


class MMPanel(Panel, Registerable):
    """
    Panel for running the Material Marshall operator.
    """

    bl_label = "Material Marshall (MM)"
    bl_idname = "VIEW3D_PT_material_marshall"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = utils.PANEL_CATEGORY

    def draw(self, context: Context):
        props = getattr(context.scene, MMProperties.bl_idname)
        col = self.layout.column()
        for propname in MMProperties.get_props():
            col.prop(props, propname)

        self.layout.operator(MMOperator.bl_idname)
