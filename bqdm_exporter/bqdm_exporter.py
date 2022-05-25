import os
import shutil
from typing import Callable, Iterable, Optional, TypeVar, cast

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import (
    Collection,
    DisplaceModifier,
    Event,
    Image,
    ImageTexture,
    Key,
    Mesh,
    Node,
    NodeLink,
    NodeTree,
    Object,
    Operator,
    ShaderNodeTexImage,
    ShapeKey,
)

# Cycles types are generated by the python API at runtime, so aren't accessible for static typing https://developer.blender.org/T68050#848508
from cycles.properties import CyclesPreferences, CyclesRenderSettings

T = TypeVar("T")


def apply_suffix(s, suffix) -> str:
    """
    Apply a suffix to a string.

    :param s: The string to suffix.
    :param suffix: The suffix to apply.
    """

    return f"{s}-{suffix}"


def search(
    current: T, is_target: Callable[[T], bool], get_children: Callable[[T], Iterable[T]]
) -> Optional[T]:
    """
    Recursively search a tree-like collection of type `T` for an element of type `T`.

    :param current: The current node being searched.
    :param is_target: A predicate function that returns True when passed the desired element.
    :param gen: A function that returns the direct children of a node when passed a node. The children should be returned as an iterable. This function should not return indirect descendants.
    :returns: the target if it was found, `None` otherwise.
    """

    found = None
    if is_target(current):
        return current
    for item in get_children(current):
        found = search(item, is_target, get_children)
        if found:
            return found
    return found


def copy_collection(src: Collection, dest: Collection, suffix="copy") -> None:
    """
    Recursively copy the contents of the collection src into the collection dest.

    :param src: The collection to copy from.
    :param dest: The collection to copy to.
    :param prefix: A string to suffix the names of copied collections and objects with.
    """

    for obj in cast(Iterable[Object], src.objects):
        obj_dup: Object = obj.copy()
        obj_dup.data = obj.data.copy()
        obj_dup.name = apply_suffix(obj.name, suffix)
        dest.objects.link(obj_dup)

    for coll in cast(Iterable[Collection], src.children):
        coll_dup = bpy.data.collections.new(apply_suffix(coll.name, suffix))
        dest.children.link(coll_dup)
        copy_collection(coll, coll_dup, suffix)


def get_node_of_type(tree: NodeTree, type: str) -> Optional[Node]:
    """
    Get the first node with type `type` from the node tree `tree`.

    :param tree: The tree to search
    :param type: The node type to search for
    :returns: the first node in `tree` with the type `type`, or None if no nodes with the given type could be found
    """

    for node in cast(Iterable[Node], tree.nodes):
        if node.type == type:
            return node
    return None


def configure_cycles(
    context: bpy.context = bpy.context,
    mode: str = "GPU",
    feature_set: str = "SUPPORTED",
    device_type="CUDA",
    samples: int = 4096,
    denoise: bool = True,
) -> None:
    """
    Activate and configure the Cycles rendering engine for rendering.

    :param context: The execution context to configure Cycles for.
    :param mode: The prefered rendering mode. Must be `"GPU"`, `"CPU"` or `"HYBRID"`.
    :param feature_set: The Cycles feature set to use.
    :param device_type: The GPU API to use for rendering. Should be `"CUDA"` or `"OPTIX"`. This will be internally applied as `"CUDA"` if running in `"HYBRID"` mode
    :param samples: The number of samples per frame.
    :param samples: Toggle denoising.
    """

    context.scene.render.engine = "CYCLES"

    cycles_settings: CyclesRenderSettings = context.scene.cycles
    cycles_settings.samples = samples
    cycles_settings.use_denoising = denoise
    if mode == "GPU" or mode == "HYBRID":
        cycles_settings.device = "GPU"
    else:
        cycles_settings.device = "CPU"

    cycles_settings.feature_set = feature_set
    if mode == "GPU":
        cycles_settings.tile_size = 256
    else:
        cycles_settings.tile_size = 16

    cycles_prefs: CyclesPreferences = context.preferences.addons["cycles"].preferences
    if mode == "CPU" or mode == "HYBRID":
        cycles_prefs.compute_device_type = "CUDA"
    else:
        cycles_prefs.compute_device_type = device_type

    # After steps (1), (2), and (3), all GPU CUDA rendering devices should be enabled and all non-GPU rendering devices should be disabled.

    # (1) Disable all rendering devices
    for device in cycles_prefs.devices:
        device.use = mode == "HYBRID"
    if mode == "HYBRID":
        return

    # (2) has_active_device() will return True if there is a GPU enabled, so we toggle all devices and test if has_active_device() reports them as a GPU or not.
    devs = []
    for device in cycles_prefs.devices:
        device.use = True
        if (mode == "GPU" and cycles_prefs.has_active_device()) or (
            mode == "CPU" and not cycles_prefs.has_active_device()
        ):
            devs.append(device)
        device.use = False
    # (3) Enable all desired devices
    for dev in devs:
        dev.use = True


def get_link(node: Node, socket_name: str, output: bool = False) -> NodeLink:
    """
    Get the first link from a socket.

    :param node: The node containing the socket.
    :param socket_name: The name of the socket.
    :param output: Should be True if the desired socket is an output socket, False otherwise
    """
    sockets = node.outputs if output else node.inputs
    return sockets[socket_name].links[0]


def find_shape_key_container(obj: Object) -> Optional[Key]:
    """
    Search `bpy.data.shape_keys` to find the Key object containing the Shape Keys for a given object

    :param current: The object who's Shape Keys are being searched for.
    :returns: the Key object if it was found, `None` otherwise.
    """

    for shape_key_container in cast(Iterable[Key], bpy.data.shape_keys):
        if shape_key_container.user == obj.data:
            return shape_key_container
    return None


class BQDMExporter(Operator):
    """Export a collection as a Baked Quasi-Dynamic Model."""

    bl_idname = "export_scene.bqdm"
    bl_label = "Export BQDM"
    NAME_SUFFIX = "BQDMEW"  # BQDM Exporter Workspace
    TEMP_DIR = "temp"
    DISP_BAKE_NAME = "DISP_BAKE"
    path: str
    disp_size_px: int

    filter_glob: StringProperty(default="*.bqdm", options={"HIDDEN"})
    target_coll_name: EnumProperty(
        name="Target Collection",
        description="Choose the collection of objects to export",
        items=lambda _scene, _context: [
            (collection.name, collection.name, "")
            for collection in cast(Iterable[Collection], bpy.data.collections)
        ],
    )
    destructive: BoolProperty(
        name="Destructive",
        description="Operate destructively and apply the computed bakes (material and geometric) to the export objects",
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

    def resolve(self, *paths: str) -> str:
        """
        Get a filepath relative to the selected export directory.

        :param paths: the paths to make relative to the export directory. Each name should be a child of the previous name

        Example: `resolve("parent", "child", "file.txt")` to construct `"[EXPORT_DIR]/parent/child/file.txt"`
        """

        return os.path.join(self.path, *paths)

    def validate_collection(self, collection: Collection) -> set[str]:
        """
        Validate a collection in preperation for a BQDM export. The collection is considered invalid if:
        - An object within the collection has no UV map
        - An object within the collection has no active material
        - The active material of an object within the collection has no Material Output node
        - The active material of an object within the collection has an empty Surface input for it's Material Output node

        :param collection: The collection to validate.

        Calls `self.error()` if the collection is deemed invalid and returns that result.
        If the collection is valid, None is returned.
        """
        for obj in cast(Iterable[Object], collection.all_objects):
            if not obj.type == "MESH":
                continue

            # Check UV Map
            mesh: Mesh = obj.data
            if not mesh.uv_layers:
                return self.error(f'Mesh "{mesh.name}" has no UV map.')

            # Check active material
            if not obj.active_material:
                return self.error(f'Object "{obj.name}" has no active material.')

            mat_tree = obj.active_material.node_tree
            output_node = get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

            # Check Material Output node
            if not output_node:
                return self.error(
                    f'Active material of the object "{obj.name}" has no Material Output node.'
                )

            # Check Surface input for Material Output node
            if not get_link(output_node, "Surface").from_socket:
                return self.error(
                    f'Active material of the object "{obj.name}" has no surface input.'
                )

    def error(self, message="Operation failed.") -> set[str]:
        """
        Report an error to Blender.
        Returns `{"CANCELLED"}`, so the return value of this function can be returned out of the operator.

        :param message: The error message to report.
        """

        self.report({"ERROR"}, message)
        return {"CANCELLED"}

    def invoke(self, context: bpy.context, _event: Event) -> set[str]:
        """
        Invoke the operator. This method is called before `execute()`, so can be used to setup initialise the operator by setting up
        it's feilds before `execute()` is run.

        :param context: The context in which the operator was invoked.
        :param event: The window event created when the operator was invoked.

        Returns `{"FINISHED"}` if the export completed successfully, {"CANCELLED"} otherwise.
        """

        # Set self.path
        blend_filepath = context.blend_data.filepath
        if not blend_filepath:
            blend_filepath = "untitled"
        else:
            blend_filepath = os.path.splitext(blend_filepath)[0]
        self.path = blend_filepath

        # Set self.disp_size_px
        self.disp_size_px = pow(2, int(self.disp_size))

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.context) -> set[str]:
        """
        Execute the operator's business logic.

        :param context: The context in which the operator was executed.

        Returns `{"FINISHED"}` if the export completed successfully, `{"CANCELLED"}` otherwise.
        """

        # Setup output directory
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        os.mkdir(self.path)
        os.mkdir(self.resolve(self.TEMP_DIR))

        # Get and validate target collection
        collection = bpy.data.collections.get(self.target_coll_name)
        validation_state = self.validate_collection(collection)
        if validation_state:
            return validation_state

        # Create workspace collection for non-descructive workflow
        if not self.destructive:
            parent_coll = search(
                context.scene.collection,
                lambda coll: collection.name in coll.children,
                lambda coll: coll.children,
            )
            workspace_coll = bpy.data.collections.new(self.NAME_SUFFIX)
            copy_collection(collection, workspace_coll, suffix=self.NAME_SUFFIX)
            collection = workspace_coll
            parent_coll.children.link(collection)

        # Set target collection to active collection (export uses active collection)
        target_layer_coll = search(
            context.view_layer.layer_collection,
            lambda layer_coll: layer_coll.name == collection.name,
            lambda layer_coll: layer_coll.children,
        )
        context.view_layer.active_layer_collection = target_layer_coll

        # Bake procedural displacement of all meshes in target collection
        configure_cycles(samples=1, denoise=False)
        context.scene.render.image_settings.file_format = "OPEN_EXR"
        context.scene.render.image_settings.color_depth = 32
        for obj in cast(Iterable[Object], collection.all_objects):
            if not obj.type == "MESH":
                continue

            # Get node tree of active material
            mat_tree = obj.active_material.node_tree
            # Get material output node of active material
            output_node = get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

            # Get the socket currently providing the surface input for the material output
            surface_socket = get_link(output_node, "Surface").from_socket
            # Get the node currently providing the displacement input for the material output
            displacement_link = get_link(output_node, "Displacement")
            # If there is no displacement source, there's no displacement so we don't have anything to bake
            if not displacement_link.from_node or not displacement_link.from_socket:
                continue
            displacement_socket = displacement_link.from_socket
            if displacement_link.from_node.type == "ShaderNodeDisplacement":
                displacement_socket = get_link(
                    displacement_link.from_node, "Height"
                ).from_socket

            # Set current object to active object for bake
            context.active_object = obj  # view_layer.objects.active = obj

            # Create emission shader node
            emission: Node = mat_tree.nodes.new("ShaderNodeEmission")
            # Connect displacment source to the emission shader's color input
            mat_tree.links.new(displacement_socket, emission.inputs["Color"])
            # Connect emission shader's output to material output's surface input socket
            mat_tree.links.new(
                emission.outputs["Emission"], output_node.inputs["Surface"]
            )

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

            # Create image texture node for to set the created image as the bake target
            img_node: ShaderNodeTexImage = mat_tree.nodes.new("ShaderNodeTexImage")
            img_node.name = self.DISP_BAKE_NAME
            img_node.select = True
            mat_tree.nodes.active = img_node
            img_node.image = img

            # Find the datablock containing this object's shape keys, if it doesn't exist can't be found, then the object has no shape keys
            # so we'll create the Basis shape key manually
            shape_key_container = find_shape_key_container(obj)
            if not shape_key_container:
                obj.shape_key_add("Basis")
                shape_key_container = find_shape_key_container(obj)

            # Bake displacement maps for all frames in the timeline, apply them as Displace modifiers, then apply the modifers as shape keys to be keyframed
            for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
                # Bake displacement map for current frame
                context.scene.frame_set(frame)
                bpy.ops.object.bake(type="EMIT", save_mode="EXTERNAL")
                img.save_render(filepath=self.resolve(self.TEMP_DIR, "baked.exr"))

                # Create and configure Displace modifier
                disp: DisplaceModifier = obj.modifiers.new(
                    apply_suffix("Displace", self.NAME_SUFFIX), type="DISPLACE"
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
                for shape_key in cast(
                    Iterable[ShapeKey], shape_key_container.key_blocks
                ):
                    if shape_key.name == disp.name:
                        break

                # "when keying data paths which contain nested properties this must be done from the `ID` subclass" - https://docs.blender.org/api/current/bpy.types.bpy_struct.html#bpy.types.bpy_struct.keyframe_insert
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

        # TODO: export particles
        # TODO: export aniamted particles?

        # TODO: uncommment
        # Export scene
        # bpy.ops.export_scene.gltf(
        #     filepath=self.resolve("model.glb"),
        #     export_image_format="NONE",
        #     export_draco_mesh_compression_enable=True,  # TODO: test different settings
        #     export_materials="NONE",
        #     export_colors=False,
        #     export_cameras=True,
        #     use_active_collection=True,
        #     export_apply=True,
        #     export_animations=True,
        # )
        #

        # TODO: uncomment
        # Delete temporary working directory
        # shutil.rmtree(self.resolve(self.TEMP_DIR))

        # TODO: uncommment
        # Cleanup workspace collection if working in non-destructive mode
        # if not self.destructive:
        #     for obj in cast(Iterable[Object], collection.all_objects):
        #         if obj.users == 1:
        #             bpy.data.objects.remove(obj)
        #     bpy.data.collections.remove(collection, do_unlink=True)

        return {"FINISHED"}
