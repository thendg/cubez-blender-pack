import os
import shutil
from typing import Iterable, cast

import bl_ui
import bpy
from ..utils import blender_utils, common_utils
from bpy.props import EnumProperty, StringProperty
from bpy.types import Collection, Context, Event, Mesh, Object
from ..utils.wrappers import CBPOperator, Registerable


class BQDMExporter(CBPOperator, Registerable):
    """Export a collection as a Baked Quasi-Dynamic Model."""

    bl_label = "Export BQDM"
    bl_idname = "export_scene.bqdm"
    menu_target = bl_ui.space_topbar.TOPBAR_MT_file_export
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

    def invoke(self, context: Context, _event: Event) -> set[str]:
        # Set self.path
        blend_filepath = context.blend_data.filepath
        if not blend_filepath:
            blend_filepath = "untitled"
        else:
            blend_filepath = os.path.splitext(blend_filepath)[0]
        self.path = blend_filepath

        # Validate the target collection
        for obj in cast(
            Iterable[Object],
            bpy.data.collections.get(self.target_coll_name).all_objects,
        ):
            if not obj.type == "MESH":
                continue

            try:
                blender_utils.check_obj(obj)
            except RuntimeError as e:
                return self.cancel(e)

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: Context) -> set[str]:
        # Setup output directory
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        os.mkdir(self.path)
        os.mkdir(self.resolve(self.TEMP_DIR))

        collection = bpy.data.collections.get(self.target_coll_name)

        # Set target collection to active collection (export uses active collection)
        target_layer_coll = common_utils.search(
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

        ##################
        # Bake materials #
        ##################

        # Configure baking settings
        blender_utils.configure_cycles(context=context, mode="HYBRID")
        context.scene.render.image_settings.file_format = "JPEG"
        context.scene.render.image_settings.color_depth = "32"

        for obj in cast(Iterable[Object], collection.all_objects):
            # TODO: srgb color space
            pass

        # Delete temporary working directory
        shutil.rmtree(self.resolve(self.TEMP_DIR))

        return {"FINISHED"}
