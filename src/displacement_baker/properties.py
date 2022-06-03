from bpy.props import BoolProperty, EnumProperty
from bpy.types import PropertyGroup

from ..utils.wrappers.registerable import Registerable


class DisplacementBakerProperties(PropertyGroup, Registerable):
    """
    A class holding the properties used by the Displacement Baker operator.
    """

    bl_label = "Displacement Baker Properties"
    bl_idname = "displacement_baker_properties"

    keep_original: BoolProperty(
        name="Keep Original", description="Keep the original object.", default=True
    )
    disp_size: EnumProperty(
        name="Displacement Map Size",
        description="The size (in pixels) of intermediate displacement maps for prodedural displacement baking",
        items=[
            ("9", "512px x 512px", "Use small displacement map textures"),
            ("10", "1024px x 1024px", "Use 1k displacement map textures"),
            ("11", "2048px x 2048px", "Use 2k displacement map textures"),
            ("12", "4096px x 4096px", "Use 3k displacement map textures"),
            ("13", "8192px x 8192px", "Use 8k displacement map textures"),
        ],
        default="9",
    )

    @staticmethod
    def get_props() -> tuple[str]:
        return "keep_original", "disp_size"
