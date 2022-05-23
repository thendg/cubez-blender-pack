import os
import shutil
from typing import Callable, Iterable, Optional, TypeVar, cast

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import (
    Collection,
    Event,
    Mesh,
    Node,
    NodeLink,
    NodeTree,
    Object,
    Operator,
    Scene,
)

T = TypeVar("T")


def search(
    current: T, is_target: Callable[[T], bool], get_children: Callable[[T], Iterable[T]]
) -> Optional[T]:
    """
    Recursively search a tree-like collection of type `T` for an element of type `T`.

    :param current: The current node being searched.
    :param is_target: A predicate function that returns True when passed the desired element.
    :param gen: A function that returns the direct children of a node when passed a node. The children should be returned as an iterable. This function should not return indirect descendants.

    Returns the target if it was found, `None` otherwise.
    """

    found = None
    if is_target(current):
        return current
    for item in get_children(current):
        found = search(item, is_target, get_children)
        if found:
            return found
    return found


def get_collections() -> list[str]:
    """Get a list of the names of all collections."""

    return [
        (collection.name, collection.name, "")
        for collection in cast(Iterable[Collection], bpy.data.collections)
    ]


def copy_collection(src: Collection, dest: Collection, suffix="copy") -> None:
    """
    Recursively copy the contents of the collection src into the collection dest.

    :param src: The collection to copy from.
    :param dest: The collection to copy to.
    :param prefix: A string to suffix the names of copied collections and objects with.
    """

    apply_suffix: Callable[[str], str] = lambda name: f"{name}-{suffix}"

    for obj in cast(Iterable[Object], src.objects):
        obj_dup: Object = obj.copy()
        obj_dup.data = obj.data.copy()
        obj_dup.name = apply_suffix(obj.name)
        dest.objects.link(obj_dup)

    for coll in cast(Iterable[Collection], src.children):
        coll_dup = bpy.data.collections.new(apply_suffix(coll.name))
        dest.children.link(coll_dup)
        copy_collection(coll, coll_dup, suffix)


def get_node_of_type(tree: NodeTree, typ: str) -> Optional[Node]:
    """
    Get the first node with type `typ` from the node tree `tree`.

    :param tree: The tree to search
    :param typ: The node type to search for

    Returns the first node in `tree` with the type `typ`, or None if no nodes
    with the given type could be found
    """

    for node in tree.nodes:
        if node.type == typ:
            return node
    return None


class BQDMExporter(Operator):
    """Export a collection in the BQDM format."""

    bl_idname = "export_scene.bqdm"
    bl_label = "Export BQDM"
    filename_ext = ".bqdm"
    bqdm_dir = ""
    workspace_suffix = "BQDMEW"  # BQDM Exporter Workspace

    def get_collections_wrapper(_scene: Scene, _context: bpy.context) -> list[str]:
        """A wrapper for `get_collections()` to allow the function to be called as a item generator for a menu property"""

        return get_collections()

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    target_coll_name: EnumProperty(
        name="Target Collection",
        description="Choose the collection of objects to export",
        items=get_collections_wrapper,
    )
    destructive: BoolProperty(
        name="Destructive",
        description="Operate destructively and apply the computed bakes (material and geometric) to the export objects",
    )

    def resolve(self, path: str) -> str:
        """Get a filepath relative to the selected export directory."""

        return os.path.join(self.bqdm_dir, path)

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
            if not cast(list[NodeLink], output_node.inputs["Surface"].links)[
                0
            ].from_socket:
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

        blend_filepath = context.blend_data.filepath
        if not blend_filepath:
            blend_filepath = "untitled"
        else:
            blend_filepath = os.path.splitext(blend_filepath)[0]

        self.filepath = blend_filepath + self.filename_ext
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.context) -> set[str]:
        """
        Execute the operator's business logic.

        :param context: The context in which the operator was executed.

        Returns `{"FINISHED"}` if the export completed successfully, `{"CANCELLED"}` otherwise.
        """

        # Setup output directory
        self.bqdm_dir = os.path.splitext(self.filepath)[0]
        if os.path.exists(self.bqdm_dir):
            shutil.rmtree(self.bqdm_dir)
        os.mkdir(self.bqdm_dir)

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
            workspace_coll = bpy.data.collections.new(self.workspace_suffix)
            copy_collection(collection, workspace_coll, suffix=self.workspace_suffix)
            collection = workspace_coll
            parent_coll.children.link(collection)

        # Set target collection to active collection (export uses active collection)
        target_layer_coll = search(
            context.view_layer.layer_collection,
            lambda layer_coll: layer_coll.name == collection.name,
            lambda layer_coll: layer_coll.children,
        )
        context.view_layer.active_layer_collection = target_layer_coll

        # Prepare Blender settings for displacement map baking
        # TODO
        # - Set cycles render device to CUDA
        # - Deselect CUDA CPU device
        # - Set cycles compute to GPU
        # - Set Rendering -> Performance -> Tiles to 8k x/y

        # Bake procedural displacement of all meshes in target collection
        for obj in cast(Iterable[Object], collection.all_objects):
            if not obj.type == "MESH":
                continue

            # get node tree of active material
            mat_tree = obj.active_material.node_tree
            # get material output node of active material
            output_node = get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

            # get the socket currently providing the surface input for the material output
            surface_src_socket = cast(
                list[NodeLink], output_node.inputs["Surface"].links
            )[0].from_socket
            # get the socket currently providing the displacement input for the material output
            displacement_src_socket = cast(
                list[NodeLink], output_node.inputs["Displacement"].links
            )[0].from_socket
            # if there is no displacement source, there's no displacement so we don't have anything to bake
            if not displacement_src_socket:
                continue

            # create emission shader node
            emission: Node = mat_tree.nodes.new("ShaderNodeEmission")
            # connect displacment source to the emission shader's color input
            mat_tree.links.new(displacement_src_socket, emission.inputs["Color"])
            # connect emission shader's output to material output's surface input socket
            mat_tree.links.new(
                emission.outputs["Emission"], output_node.inputs["Surface"]
            )

            context.scene.frame_set(1)

            # - (*) Create new image texture referencing a 32 float bit 8k texture
            # - Bake an emission map to the image
            # - Save the image to a 32 bit float exr
            # - Add displace modifier
            # - Set Displace Modifier -> Texture Coordinates to "UV"
            # - Set Displace Modifier -> Direction to "RGB to XYZ"
            # - Load emisssion map into displace modifier
            # - Apply modifier as shape key
            # - Set modifier blend value to 0 for frame - 1
            # - Set modifier blend value to 1 for frame
            # - Set modifier blend value to 0 for frame + 1
            # - Delete the exr file and 8k image
            # - Increment frame and return to (*)

            mat_tree.nodes.remove(emission)
            # put the original surface shader back as the surface input for the material output
            mat_tree.links.new(surface_src_socket, output_node.inputs["Surface"])

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

        # if not self.destructive:
        #     for obj in cast(Iterable[Object], collection.all_objects):
        #         if obj.users == 1:
        #             bpy.data.objects.remove(obj)
        #     bpy.data.collections.remove(collection, do_unlink=True)

        return {"FINISHED"}

    def menu_func_export(self, _context: bpy.context):
        """Called to extend the file export menu window with the BQDM Exporter's parameters"""

        self.layout.operator(BQDMExporter.bl_idname, text="BQDM (.bqdm)")
