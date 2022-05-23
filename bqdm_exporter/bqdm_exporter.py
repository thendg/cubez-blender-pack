import os
import shutil
from typing import Callable, Iterable, TypeVar, cast

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Collection, Event, Mesh, Object, Operator, Scene

T = TypeVar("T")


def search(
    current: T, is_target: Callable[[T], bool], get_children: Callable[[T], Iterable[T]]
) -> T | None:
    """
    Recursively search a tree-like collection of type T for an element of type T.

    :param current: The current node being searched
    :param is_target: A predicate function that returns True when passed the desired element
    :param gen: A function that returns the direct children of a node when passed a node. The children should be returned as an iterable. This function should not return indirect children.

    Returns the target if it was found, None otherwise.
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

    :param src: The collection to copy from
    :param dest: The collection to copy to
    :param prefix: A string to suffix the names of copied collections and objects with
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


class BQDMExporter(Operator):
    """Export a collection in the BQDM format."""

    bl_idname = "export_scene.bqdm"
    bl_label = "Export BQDM"
    filename_ext = ".bqdm"
    bqdm_dir = ""
    workspace_suffix = "BQDMEW"  # BQDM Exporter Workspace

    def get_collections_wrapper(_scene: Scene, _context: bpy.context) -> list[str]:
        """A wrapper for the get_collections() function to allow the function to be called as a item generator for a menu property"""

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
        """Get a filepath relative to the selected export directory"""

        return os.path.join(self.bqdm_dir, path)

    def invoke(self, context: bpy.context, _event: Event) -> set[str]:
        """
        Invoke the operator. This method is called before execute(), so can be used to setup initialise the operator by setting up
        it's feilds before execute() is run.

        :param context: The context in which the operator was invoked
        :param event: The window event created when the operator was invoked
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
        self.bqdm_dir = os.path.splitext(self.filepath)[0]
        if os.path.exists(self.bqdm_dir):
            shutil.rmtree(self.bqdm_dir)
        os.mkdir(self.bqdm_dir)

        collection = bpy.data.collections.get(self.target_coll_name)

        for mesh in cast(
            Iterable[Mesh],
            [
                obj.data
                for obj in cast(Iterable[Object], collection.all_objects)
                if obj.type == "MESH"
            ],
        ):
            if not mesh.uv_layers:
                self.report({"ERROR"}, f'Mesh "{mesh.name}" has no UV map')
                return {"CANCELLED"}

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

        target_layer_coll = search(
            context.view_layer.layer_collection,
            lambda layer_coll: layer_coll.name == collection.name,
            lambda layer_coll: layer_coll.children,
        )
        context.view_layer.active_layer_collection = target_layer_coll

        for obj in cast(Iterable[Object], collection.all_objects):
            # Bake procedural displacement
            # - Set frame to 1
            # - Find the node creating the displacement (the node plugged into the displacement input on the Material Output node)
            # - Connect the displacment creator node into an emission node
            # - Connect the emission shader node into the Material Output node
            # - Set cycles render device to CUDA
            # - Deselect CUDA CPU device
            # - Set cycles compute to GPU
            # - Set Rendering -> Performance -> Tiles to 8k x/y

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
            pass

        bpy.ops.export_scene.gltf(
            filepath=self.resolve("model.glb"),
            export_image_format="NONE",
            export_draco_mesh_compression_enable=True,  # TODO: test different settings
            export_materials="NONE",
            export_colors=False,
            export_cameras=True,
            use_active_collection=True,
            export_apply=True,
            export_animations=True,
        )

        if not self.destructive:
            for obj in cast(Iterable[Object], collection.all_objects):
                if obj.users == 1:
                    bpy.data.objects.remove(obj)
            bpy.data.collections.remove(collection, do_unlink=True)

        return {"FINISHED"}

    def menu_func_export(self, _context: bpy.context):
        """Called to extend the file export menu window with the BQDM Exporter's parameters"""

        self.layout.operator(BQDMExporter.bl_idname, text="BQDM (.bqdm)")
