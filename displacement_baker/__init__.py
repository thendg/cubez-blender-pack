# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from typing import Callable

import bpy
from bpy.types import Context, Menu, TOPBAR_MT_file_export

from .. import utils
from .displacement_baker import DisplacementBaker

bl_info = {
    "name": "BQDM Exporter",
    "description": "Export scenes in the BQDM format",
    "author": "NOIR Development Group",
    "version": (1, 0, 0),  # ALPHA
    "blender": (3, 1, 0),
    # "location": "File > Export",
    "warning": "",  # used for warning users of bug or problems with the addon. shows up in the addons panel
    "doc_url": "",  # TODO: populate
    "tracker_url": "",  # TODO: populate
    "support": "COMMUNITY",
    "category": "Import-Export",
}

mfe: Callable[[Menu, Context], None] = lambda caller, _context: utils.menu_func_export(
    caller, DisplacementBaker.bl_idname, text="BQDM (.bqdm)"
)


def register():
    "Register the exporter class with Blender and an export option to the export menu"

    bpy.utils.register_class(DisplacementBaker)
    TOPBAR_MT_file_export.append(mfe)


def unregister():
    "Unregister the exporter class and remove the export option from the export menu"

    bpy.utils.unregister_class(DisplacementBaker)
    TOPBAR_MT_file_export.remove(mfe)
