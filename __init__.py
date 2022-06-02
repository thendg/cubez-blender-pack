from typing import Callable, Type

from bpy.types import Context, Menu, Operator

# The relative import implicitly registers the import classes too - equivalent to using bpy.utils.[register/unregister]_class
from .bqdm_exporter import BQDMExporter
from .displacement_baker import DisplacementBaker
from .utils import CubezOperator

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
classes: list[Type[CubezOperator]] = [BQDMExporter, DisplacementBaker]


def get_menu_func(cls: Type[Operator]) -> Callable[[Menu, Context], None]:
    """
    Return a function that binds a button or trigger on a UILayout to the relevant class' `invoke()` method.
    Signature follows the requirements for this function to be passed as a draw function to a UI component.

    :param cls: The class to register.
    """
    return lambda caller, _context: caller.layout.operator(
        cls.bl_idname, text=cls.bl_label
    )


def register():
    "Append classes to their associated menus."
    for cls in [cls for cls in classes if cls.menu_target]:
        cls.menu_target.append(get_menu_func(cls))


def unregister():
    "Remove classes from their associated menus."
    for cls in [cls for cls in classes if cls.menu_target]:
        cls.menu_target.remove(get_menu_func(cls))


if __name__ == "__main__":
    register()
