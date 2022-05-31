import os
from typing import Iterable, cast

import bpy
from bpy.props import BoolProperty, EnumProperty
from bpy.types import (
    Context,
    DisplaceModifier,
    Event,
    Image,
    ImageTexture,
    Node,
    Object,
    Operator,
    ShaderNodeTexImage,
    ShapeKey,
)

from .. import utils


class DisplacementBaker(Operator):
    """Bake the procedural displacement of an object into animated shape keys."""

    bl_idname = "export_scene.bqdm"  # TODO: update
    bl_label = "Bake Procedural Displacement"  # TODO: update
    DISP_BAKE_NAME = "DISP_BAKE"
    disp_size_px: int

    # TODO: change to "keep original"
    keep_original: BoolProperty(
        name="Keep Original",
        description="Keep the original object.",
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

    def error(self, message="Operation failed.") -> set[str]:
        """
        Report an error to Blender.
        Returns `{"CANCELLED"}`, so the return value of this function can be returned out of the operator.

        :param message: The error message to report.
        """

        self.report({"ERROR"}, message)
        return {"CANCELLED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        """
        Invoke the operator. This method is called before `execute()`, so can be used to setup initialise the operator by setting up
        it's feilds before `execute()` is run.

        :param context: The context in which the operator was invoked.
        :param event: The window event created when the operator was invoked.

        Returns `{"FINISHED"}` if the export completed successfully, {"CANCELLED"} otherwise.
        """

        self.disp_size_px = pow(2, int(self.disp_size))
        return {"RUNNING_MODAL"}

    def execute(self, context: Context) -> set[str]:
        """
        Execute the operator's business logic.

        :param context: The context in which the operator was executed.

        Returns `{"FINISHED"}` if the export completed successfully, `{"CANCELLED"}` otherwise.
        """

        # Configure baking settings
        utils.configure_cycles(samples=1, denoise=False)
        context.scene.render.image_settings.file_format = "OPEN_EXR"
        context.scene.render.image_settings.color_depth = 32

        # Get target object
        obj = context.active_object
        if self.keep_original:
            parent_collection = utils.search(
                context.scene,
                lambda coll: obj.name in coll.objects,
                lambda coll: coll.objects,
            )
            obj_dup = obj.copy()
            obj_dup.data = obj.data.copy()
            parent_collection.objects.link(obj_dup)
            obj = obj_dup

        if not obj.type == "MESH":
            return {"FINISHED"}

        #############################################
        # Inspect active material of current object #
        #############################################

        mat_tree = obj.active_material.node_tree
        output_node = utils.get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

        # Get the socket providing the surface input for the material output
        surface_socket = utils.get_link(output_node, "Surface").from_socket
        # Get the node providing the displacement input for the material output
        displacement_link = utils.get_link(output_node, "Displacement")
        # If there is no displacement source, there's no displacement so we don't have anything to bake for this stage
        if not displacement_link.from_node or not displacement_link.from_socket:
            return {"FINISHED"}
        # Get the socket providing the displacement input for the material output
        displacement_socket = displacement_link.from_socket
        # If the displacement source node is a displacement node, backtrack to the Height input for the displacement source
        # because displacement output is not going to give us the right output for baking a displacement map (we need a greyscale image).
        if displacement_link.from_node.type == "ShaderNodeDisplacement":
            displacement_socket = utils.get_link(
                displacement_link.from_node, "Height"
            ).from_socket

        # Set current object to active object for bake
        # TODO: might have to be: view_layer.objects.active = obj
        context.active_object = obj

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
            self.disp_size_px,
            self.disp_size_px,
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
        shape_key_container = utils.find_shape_key_container(obj)
        if not shape_key_container:
            obj.shape_key_add("Basis")
            shape_key_container = utils.find_shape_key_container(obj)

        ###################################################################
        # Bake and apply displacement maps for all frames in the timeline #
        ###################################################################

        for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
            # Bake displacement map for current frame
            context.scene.frame_set(frame)
            bpy.ops.object.bake(type="EMIT", save_mode="EXTERNAL")
            img.save_render(
                filepath=self.resolve(self.TEMP_DIR, "baked.exr")
            )  # TODO: use temp dir

            # Create and configure Displace modifier
            disp: DisplaceModifier = obj.modifiers.new(
                utils.apply_suffix("Displace", self.NAME_SUFFIX), type="DISPLACE"
            )
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
            for shape_key in cast(Iterable[ShapeKey], shape_key_container.key_blocks):
                if shape_key.name == disp.name:
                    break

            # "when keying data paths which contain nested properties this must be done from the `ID` subclass"
            # - https://docs.blender.org/api/current/bpy.types.bpy_struct.html#bpy.types.bpy_struct.keyframe_insert
            data_path = f'key_blocks["{shape_key.name}"].value'

            # Animate Shape Key
            shape_key.value = 0.0
            shape_key_container.keyframe_insert(data_path=data_path, frame=frame - 1)
            shape_key.value = 1.0
            shape_key_container.keyframe_insert(data_path=data_path, frame=frame)
            shape_key.value = 0.0
            shape_key_container.keyframe_insert(data_path=data_path, frame=frame + 1)

        # Remove extra material nodes
        mat_tree.nodes.remove(emission)
        mat_tree.nodes.remove(img_node)
        # Put the original surface shader back as the surface input for the material output
        mat_tree.links.new(surface_socket, output_node.inputs["Surface"])

        # Delete dispalcement map image/texture blend data (the saved render will get cleaned up later)
        bpy.data.images.remove(img)
        bpy.data.textures.remove(tex)

        return {"FINISHED"}
