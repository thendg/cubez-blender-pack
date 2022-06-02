from bpy.types import Context, Panel

from ..utils.wrappers import Registerable


class DisplacementBakerPanel(Panel, Registerable):
    """Bake the procedural displacement of an object into animated shape keys."""

    bl_label = "Displacement Baker"
    bl_idname = "VIEW3D_PT_displacement_baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cubez Blender Pack"

    # TODO: bake from modifier
    # TODO: bake from nodes

    def draw(self, context: Context):

        self.layout.label(text="Hello, World!")
