from abc import ABC
from typing import Optional, Type

import bpy_types


class Registerable(ABC):
    """
    A base class defining some properties used for class registration in with Blender's Python interface
    """

    bl_label: str
    bl_idname: str
    menu_target: Optional[Type[bpy_types.Menu]] = None
