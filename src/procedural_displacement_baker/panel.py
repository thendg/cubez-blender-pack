from bpy.types import Context, Panel

import utils
from ..utils.wrappers import Registerable
from .operator import PDBOperator
from .properties import PDBProperties


class PDBPanel(Panel, Registerable):
    """
    Panel for running the Displacement Baker operator.
    """

    bl_label = "Procedural Displacement Baker (PDB)"
    bl_idname = "VIEW3D_PT_displacement_baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = utils.PANEL_CATEGORY

    def draw(self, context: Context):
        props = getattr(context.scene, PDBProperties.bl_idname)
        col = self.layout.column()
        for propname in PDBProperties.get_props():
            col.prop(props, propname)

        self.layout.operator(PDBOperator.bl_idname)
