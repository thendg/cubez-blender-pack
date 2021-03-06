from bpy.props import BoolProperty, EnumProperty
from bpy.types import PropertyGroup

from ..utils.wrappers.registerable import Registerable


class MMProperties(PropertyGroup, Registerable):
    """
    A class holding the properties used by the Material Marshall operator.
    """

    bl_label = "Material Marshall Properties"
    bl_idname = "material_marshall_properties"

    keep_original: BoolProperty(
        name="Keep Original", description="Keep the original object.", default=True
    )
    is_animated: BoolProperty(
        name="Animated",
        description="Should be selected only if the object has animated displacement. If the object is animated but the displacement is not, or object is completely static, this options should be left unchecked.",
        default=False,
    )
    disp_size: EnumProperty(
        name="Displacement Map Size",
        description="The size (in pixels) of intermediate displacement maps for prodedural displacement baking",
        items=[
            ("7", "128px x 128px", "Use 128px textures"),
            ("8", "256px x 256px", "Use 256px textures"),
            ("9", "512px x 512px", "Use 512px textures"),
            ("10", "1024px x 1024px", "Use 1k textures"),
            ("11", "2048px x 2048px", "Use 2k textures"),
            ("12", "4096px x 4096px", "Use 4k textures"),
            ("13", "8192px x 8192px", "Use 8k textures"),  # TODO: refactor into utils
        ],
        default="7",
    )

    @staticmethod
    def get_props() -> tuple[str]:
        return "keep_original", "is_animated", "disp_size"
