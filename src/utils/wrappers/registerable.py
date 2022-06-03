from typing import Optional, Type

import bpy_types


class Registerable:
    """
    A base class defining some attributes used for class registration in with Blender's Python interface
    """

    bl_label: str
    bl_idname: str
    menu_target: Optional[Type[bpy_types.Menu]] = None
