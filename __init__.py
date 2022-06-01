# The relative import implicitly registers the import classes too - equivalent to using bpy.utils.[register/unregister]_class
from typing import Callable, Type

from bpy.types import Context, Menu

from .bqdm_exporter import BQDMExporter
from .displacement_baker import DisplacementBaker
from .types import CubezOperator

bl_info = {
    "name": "Cubez Blender Pack",
    "description": "A collection of helpers designed by the Cubez.io team for development in blender",
    "author": "NOIR Development Group",
    "version": (1, 0, 0),  # ALPHA
    "blender": (3, 1, 0),
    "warning": "",  # used for warning users of bug or problems with the addon. shows up in the addons panel
    "doc_url": "",  # TODO: populate
    "tracker_url": "",  # TODO: populate
    "support": "COMMUNITY",
}

classes: list[Type[CubezOperator]] = [BQDMExporter, DisplacementBaker]


def get_menu_func(idname: str, label: str) -> Callable[[Menu, Context], None]:
    """
    Return a function that binds a button or trigger on a UILayout to the relevant class' `invoke()` method.
    Signature follows the requirements for this function to be passed as a draw function to a UI component.

    :param idname: The bl_idname of the class to register.
    :param label: The bl_label of the class to register.
    """
    return lambda caller, _context: caller.layout.operator(idname, text=label)


def register():
    "Append classes to their associated menus."
    for cls in [cls for cls in classes if cls.get_menu_target()]:
        cls.get_menu_target().append(get_menu_func(cls))


def unregister():
    "Remove classes from their associated menus."
    for cls in [cls for cls in classes if cls.get_menu_target()]:
        cls.get_menu_target().remove(get_menu_func(cls))


if __name__ == "__main__":
    register()
