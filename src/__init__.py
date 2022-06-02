from typing import Callable, Type
import bpy

from bpy.types import Context, Menu

from .bqdm_exporter import BQDMExporter
from .displacement_baker import DisplacementBakerOperator, DisplacementBakerPanel
from .utils.wrappers import Registerable

# addon metadata
bl_info = {
    "name": "Cubez Blender Pack",
    "description": "A collection of helpers designed by the Cubez.io team for development in Blender",
    "author": "NOIR Development Group",
    "version": (1, 0, 0),
    "blender": (3, 1, 0),
    "warning": "This is an ALPHA version of the Cubez Blender Pack",
    "doc_url": "https://github.com/thendg/cubez-packages#readme",
    "tracker_url": "https://github.com/thendg/cubez-packages/issues",
    "support": "COMMUNITY",
}
# operator subclasses to register
CLASSES: list[Type[Registerable]] = [
    BQDMExporter,
    DisplacementBakerOperator,
    DisplacementBakerPanel,
]
# dictionary of operators to their draw functions
menu_funcs: dict[Type[Registerable], Callable[[Menu, Context], None]] = {}


def register():
    "Register classes and append them to their associated menus."

    for cls in CLASSES:
        print(f"[[CBP]] - Registered: {cls}")
        bpy.utils.register_class(cls)
        if cls.menu_target:
            menu_funcs[cls] = lambda caller, _context: caller.layout.operator(
                cls.bl_idname, text=cls.bl_label
            )
            cls.menu_target.append(menu_funcs[cls])


def unregister():
    "Unregister classes and remove them from their associated menus."

    for cls in CLASSES:
        print(f"[[CBP]] - Unregistered: {cls}")
        bpy.utils.unregister_class(cls)
        if cls.menu_target:
            cls.menu_target.remove(menu_funcs[cls])


if __name__ == "__main__":
    register()
