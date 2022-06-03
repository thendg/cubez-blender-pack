import tempfile
from typing import Iterable, cast

import bpy
from bpy.types import (
    Context,
    DisplaceModifier,
    Event,
    Image,
    ImageTexture,
    Node,
    Object,
    ShaderNodeTexImage,
    ShapeKey,
)

from ..utils.wrappers import CBPOperator, Registerable
from ..utils import blender_utils, common_utils
from .properties import DisplacementBakerProperties


class DisplacementBakerOperator(CBPOperator, Registerable):
    """Bake the procedural displacement of an object into animated shape keys."""

    bl_label = "Bake Procedural Displacement"
    bl_idname = "object.bake_procedural_displacement"
    DISP_BAKE_NAME = "DISP_BAKE"
    keep_original: bool
    disp_size: int

    @classmethod
    def poll(cls, context: Context):
        return context.view_layer.objects.active.mode == "OBJECT"

    def invoke(self, context: Context, _event: Event) -> set[str]:
        props: DisplacementBakerProperties = getattr(
            context.scene, DisplacementBakerProperties.bl_idname
        )
        self.keep_original = props.keep_original
        self.disp_size = pow(2, int(props.disp_size))
        return {"RUNNING_MODAL"}

    def execute(self, context: Context) -> set[str]:
        # Configure baking settings
        blender_utils.configure_cycles(samples=1, denoise=False)
        context.scene.render.image_settings.file_format = "OPEN_EXR"
        context.scene.render.image_settings.color_depth = 32

        # Get target object
        obj = context.view_layer.objects.active
        if self.keep_original:
            parent_collection = common_utils.search(
                context.scene.collection,
                lambda coll: obj.name in coll.objects,
                lambda coll: coll.children,
            )
            obj_dup: Object = obj.copy()
            obj_dup.data = obj.data.copy()
            parent_collection.objects.link(obj_dup)
            obj = obj_dup

        if not obj.type == "MESH":
            return {"FINISHED"}

        #############################################
        # Inspect active material of current object #
        #############################################

        mat_tree = obj.active_material.node_tree
        output_node = blender_utils.get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

        # Get the socket providing the surface input for the material output
        surface_socket = blender_utils.get_link(output_node, "Surface").from_socket
        # Get the node providing the displacement input for the material output
        displacement_link = blender_utils.get_link(output_node, "Displacement")
        # If there is no displacement source, there's no displacement so we don't have anything to bake for this stage
        if not displacement_link.from_node or not displacement_link.from_socket:
            return {"FINISHED"}
        # Get the socket providing the displacement input for the material output
        displacement_socket = displacement_link.from_socket
        # If the displacement source node is a displacement node, backtrack to the Height input for the displacement source
        # because displacement output is not going to give us the right output for baking a displacement map (we need a greyscale image).
        if displacement_link.from_node.type == "ShaderNodeDisplacement":
            displacement_socket = blender_utils.get_link(
                displacement_link.from_node, "Height"
            ).from_socket

        ###############################
        # Prepare material for baking #
        ###############################

        # Create emission shader node
        emission: Node = mat_tree.nodes.new("ShaderNodeEmission")
        # Connect displacment source to the emission shader's color input
        mat_tree.links.new(displacement_socket, emission.inputs["Color"])
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

        # Create image texture
        tex: ImageTexture = bpy.data.textures.new(self.DISP_BAKE_NAME, type="IMAGE")
        tex.image = img

        # Create image texture node to set the created image as the bake target
        img_node: ShaderNodeTexImage = mat_tree.nodes.new("ShaderNodeTexImage")
        img_node.name = self.DISP_BAKE_NAME
        img_node.select = True
        mat_tree.nodes.active = img_node
        img_node.image = img

        # Find the datablock containing this object's shape keys, if it doesn't exist can't be found, then the object has no shape keys
        # so we'll create the Basis shape key manually
        shape_key_container = blender_utils.find_shape_key_container(obj)
        if not shape_key_container:
            obj.shape_key_add("Basis")
            shape_key_container = blender_utils.find_shape_key_container(obj)

        ###################################################################
        # Bake and apply displacement maps for all frames in the timeline #
        ###################################################################

        with tempfile.NamedTemporaryFile() as img_file:
            for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
                # Bake displacement map for current frame
                context.scene.frame_set(frame)
                bpy.ops.object.bake(type="EMIT", save_mode="EXTERNAL")
                img.save_render(filepath=img_file.name)

                # Create and configure Displace modifier
                disp: DisplaceModifier = obj.modifiers.new("Displace", "DISPLACE")
                disp.space = "LOCAL"
                disp.texture_coords = "UV"
                disp.direction = "RGB_TO_XYZ"
                disp.texture = tex
                disp.is_active = True

                # Apply modifier as Shape Key
                bpy.ops.object.modifier_apply_as_shapekey(
                    keep_modifier=False, modifier=disp.name
                )

                # Find the newly created shape key
                shape_key: ShapeKey = None
                for shape_key in cast(
                    Iterable[ShapeKey], shape_key_container.key_blocks
                ):
                    if shape_key.name == disp.name:
                        break

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

        # Remove extra material nodes
        mat_tree.nodes.remove(emission)
        mat_tree.nodes.remove(img_node)
        # Put the original surface shader back as the surface input for the material output
        mat_tree.links.new(surface_socket, output_node.inputs["Surface"])

        # Delete dispalcement map image/texture blend data (the saved render will get cleaned up later)
        bpy.data.images.remove(img)
        bpy.data.textures.remove(tex)

        return {"FINISHED"}
