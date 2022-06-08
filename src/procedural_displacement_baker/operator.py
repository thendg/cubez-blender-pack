from typing import Iterable, cast

import bpy
from bpy.types import (
    Context,
    DisplaceModifier,
    Event,
    Image,
    ImageTexture,
    MaterialSlot,
    Node,
    NodeSocketFloat,
    Object,
    ShaderNodeTexImage,
    ShapeKey,
)

from ..utils.wrappers import CBPOperator, Registerable
from ..utils import blender_utils, render_utils, common_utils
from .properties import PDBProperties


def setup_displace_modifier(
    mod: DisplaceModifier,
    tex: ImageTexture,
    mid_level: float = 0.5,
    strength: float = 1,
):
    """
    Setup a Displace modifier to read from a baked displacement map.

    :param mod: The modifier to setup
    :param tex: The texture to read from
    :param mid_level: The Midlevel value to apply to the modifier
    :param strength: The Strength value to apply to the modifier
    """

    mod.space = "LOCAL"
    mod.texture_coords = "UV"
    mod.direction = "RGB_TO_XYZ"
    mod.mid_level = mid_level
    mod.strength = strength
    mod.texture = tex
    mod.is_active = True


class PDBOperator(CBPOperator, Registerable):
    """Bake the procedural displacement of an object into animated shape keys."""

    bl_label = "Bake Procedural Displacement"
    bl_idname = "object.bake_procedural_displacement"
    DISP_BAKE_NAME = "DISP_BAKE"
    keep_original: bool
    is_animated: bool
    disp_size: int

    @classmethod
    def poll(cls, context: Context):
        obj = context.view_layer.objects.active
        return obj and obj.mode == "OBJECT" and obj.type == "MESH"

    def invoke(self, context: Context, _event: Event) -> set[str]:
        # Get active object
        obj = context.view_layer.objects.active

        # Check that object can be worked with
        try:
            blender_utils.check_obj(obj)
        except RuntimeError as e:
            return self.cancel(e)

        # Get object's material for analysis
        mat_tree = obj.active_material.node_tree
        output_node = blender_utils.get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

        # If there is no displacement source, there's no displacement so we don't have anything to bake
        if not blender_utils.get_link(output_node, "Displacement"):
            return self.cancel(
                "Operation cancelled because active object has no displacement source in active material."
            )

        # Read operator properties
        props: PDBProperties = getattr(context.scene, PDBProperties.bl_idname)
        self.keep_original = props.keep_original
        self.is_animated = props.is_animated
        self.disp_size = pow(2, int(props.disp_size))

        try:
            return self.execute(context)
        except RuntimeError as e:
            return self.error(e)

    def execute(self, context: Context) -> set[str]:
        # Configure baking settings
        reset_cb = render_utils.get_config_resetter(context)
        render_utils.configure_cycles(context=context, samples=1, denoise=False)
        context.scene.render.image_settings.file_format = "OPEN_EXR"
        context.scene.render.image_settings.color_depth = "32"

        # Get target object
        obj = context.view_layer.objects.active

        # Duplicate object if working non-destructively
        if self.keep_original:
            # TODO: rename duplicate with self.DISP_BAKE_NAME
            parent_collection = common_utils.search(
                context.scene.collection,
                lambda coll: obj.name in coll.objects,
                lambda coll: coll.children,
            )
            obj_dup: Object = obj.copy()
            obj_dup.data = obj.data.copy()
            for mat_slot in cast(Iterable[MaterialSlot], obj.material_slots):
                obj_dup.material_slots[
                    mat_slot.name
                ].material = mat_slot.material.copy()
            obj.hide_set(True)
            obj.hide_render = True
            parent_collection.objects.link(obj_dup)
            context.view_layer.objects.active = obj_dup
            obj = obj_dup

        # Enable object
        obj.select_set(True)
        obj.hide_set(False)
        obj.hide_render = False

        #############################################
        # Inspect active material of current object #
        #############################################

        mat_tree = obj.active_material.node_tree
        output_node = blender_utils.get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

        # Get the socket providing the surface input for the material output
        surface_socket = blender_utils.get_link(output_node, "Surface").from_socket
        # Get the displacement node providing the displacement input for the material output
        displacement_link = blender_utils.get_link(output_node, "Displacement")
        displacement_node = displacement_link.from_node
        # Displacement output is not going to give us the right output for baking a displacement map (we need a greyscale image) so
        # we'll get the height source.
        height_socket = blender_utils.get_link(displacement_node, "Height").from_socket

        # Get scale and midlevel from displacement node
        disp_scale = cast(
            NodeSocketFloat, displacement_node.inputs["Scale"]
        ).default_value
        disp_midlevel = cast(
            NodeSocketFloat, displacement_node.inputs["Midlevel"]
        ).default_value

        ###############################
        # Prepare material for baking #
        ###############################

        # Create emission shader node
        emission: Node = mat_tree.nodes.new("ShaderNodeEmission")
        # Connect displacment source to the emission shader's color input
        mat_tree.links.new(height_socket, emission.inputs["Color"])
        # Connect emission shader's output to material output's surface input socket
        mat_tree.links.new(emission.outputs["Emission"], output_node.inputs["Surface"])

        ###########################
        # Create baking resources #
        ###########################

        # Create bake image
        img: Image = bpy.data.images.new(
            self.DISP_BAKE_NAME,
            self.disp_size,
            self.disp_size,
            float_buffer=True,
            is_data=True,
        )
        img.colorspace_settings.name = "Non-Color"

        # Create image texture
        tex: ImageTexture = bpy.data.textures.new(self.DISP_BAKE_NAME, type="IMAGE")
        tex.image = img

        # Create image texture node to set the created image as the bake target
        img_node: ShaderNodeTexImage = mat_tree.nodes.new("ShaderNodeTexImage")
        img_node.name = self.DISP_BAKE_NAME
        img_node.select = True
        mat_tree.nodes.active = img_node
        img_node.image = img

        # Boolean value to represent a displace modifer has been applied
        applied = False
        if self.is_animated:
            applied = True

            # Find the datablock containing this object's shape keys, if it doesn't exist can't be found, then the object has no shape keys
            # so we'll create the Basis shape key manually
            shape_key_container = blender_utils.find_shape_key_container(obj)
            if not shape_key_container:
                obj.shape_key_add(name="Basis")
                shape_key_container = blender_utils.find_shape_key_container(obj)

            # Bake and apply displacement maps for all frames in the timeline
            for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
                # Bake displacement map for current frame
                context.scene.frame_set(frame)
                bpy.ops.object.bake(type="EMIT")

                # Create and configure Displace modifier
                # Store the name for later comparison instead of using DisplaceModifier.name to avoid https://blender.stackexchange.com/questions/192995/utf-8-codec-cant-decode-strings-randomly
                name = f"Displace-{frame}"
                disp: DisplaceModifier = obj.modifiers.new(name, "DISPLACE")
                setup_displace_modifier(
                    disp, tex, mid_level=disp_midlevel, strength=disp_scale
                )

                # Apply modifier as Shape Key
                bpy.ops.object.modifier_apply_as_shapekey(
                    keep_modifier=False, modifier=disp.name
                )

                # Find the newly created shape key
                shape_key: ShapeKey = None
                for shape_key in cast(
                    Iterable[ShapeKey], shape_key_container.key_blocks
                ):
                    if shape_key.name == name:
                        break

                if shape_key is None:
                    self.error(f"Failed to shape key created for frame [{frame}]")

                # "when keying data paths which contain nested properties this must be done from the `ID` subclass"
                # - https://docs.blender.org/api/current/bpy.types.bpy_struct.html#bpy.types.bpy_struct.keyframe_insert
                data_path = f'key_blocks["{shape_key.name}"].value'

                # Animate Shape Key
                shape_key.value = 0.0
                shape_key_container.keyframe_insert(
                    data_path=data_path, frame=frame - 1
                )
                shape_key.value = 1.0
                shape_key_container.keyframe_insert(data_path=data_path, frame=frame)
                shape_key.value = 0.0
                shape_key_container.keyframe_insert(
                    data_path=data_path, frame=frame + 1
                )
        else:
            ###############################################################
            # Bake one map and create a displace modifier to read from it #
            ###############################################################
            bpy.ops.object.bake(type="EMIT")
            disp: DisplaceModifier = obj.modifiers.new("Displace", "DISPLACE")
            setup_displace_modifier(
                disp, tex, mid_level=disp_midlevel, strength=disp_scale
            )

        # Reset render engine settings
        reset_cb(context)

        # Remove extra material nodes
        mat_tree.nodes.remove(emission)
        mat_tree.nodes.remove(img_node)
        # Put the original surface shader back as the surface input for the material output
        mat_tree.links.new(surface_socket, output_node.inputs["Surface"])
        # Unlink procedural displacement
        mat_tree.links.remove(displacement_link)

        if applied:
            # Delete dispalcement map image/texture blend data (the saved render will get cleaned up later)
            bpy.data.images.remove(img)
            bpy.data.textures.remove(tex)

        return {"FINISHED"}
