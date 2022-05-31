import os
import shutil
from typing import Iterable, cast

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Collection, Context, Event, Mesh, Object, Operator

from .. import utils


class BQDMExporter(Operator):
    """Export a collection as a Baked Quasi-Dynamic Model."""

    bl_idname = "export_scene.bqdm"
    bl_label = "Export BQDM"
    TEMP_DIR = "temp"
    path: str

    filter_glob: StringProperty(default="*.bqdm", options={"HIDDEN"})
    target_coll_name: EnumProperty(
        name="Target Collection",
        description="Choose the collection of objects to export",
        items=lambda _scene, _context: [
            (collection.name, collection.name, "")
            for collection in cast(Iterable[Collection], bpy.data.collections)
        ],
    )

    def resolve(self, *paths: str) -> str:
        """
        Get a filepath relative to the selected export directory.

        :param paths: the paths to make relative to the export directory. Each name should be a child of the previous name

        Example: `resolve("parent", "child", "file.txt")` to construct `"[EXPORT_DIR]/parent/child/file.txt"`
        """

        return os.path.join(self.path, *paths)

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

        # Set self.path
        blend_filepath = context.blend_data.filepath
        if not blend_filepath:
            blend_filepath = "untitled"
        else:
            blend_filepath = os.path.splitext(blend_filepath)[0]
        self.path = blend_filepath

        ##################################
        # Validate the target collection #
        ##################################
        for obj in cast(
            Iterable[Object],
            bpy.data.collections.get(self.target_coll_name).all_objects,
        ):
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
            output_node = utils.get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

            # Check Material Output node
            if not output_node:
                return self.error(
                    f'Active material of the object "{obj.name}" has no Material Output node.'
                )

            # Check Surface input for Material Output node
            if not utils.get_link(output_node, "Surface").from_socket:
                return self.error(
                    f'Active material of the object "{obj.name}" has no surface input.'
                )

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: Context) -> set[str]:
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

        collection = bpy.data.collections.get(self.target_coll_name)

        # Set target collection to active collection (export uses active collection)
        target_layer_coll = utils.search(
            context.view_layer.layer_collection,
            lambda layer_coll: layer_coll.name == collection.name,
            lambda layer_coll: layer_coll.children,
        )
        context.view_layer.active_layer_collection = target_layer_coll

        # Export scene
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

        # Delete temporary working directory
        shutil.rmtree(self.resolve(self.TEMP_DIR))

        return {"FINISHED"}
