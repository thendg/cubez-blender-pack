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

import bpy
from .bqdm_exporter import BQDMExporter
from bpy.types import Menu, TOPBAR_MT_file_export

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


# explaination of `caller` param https://blender.stackexchange.com/q/42907
def menu_func_export(caller: Menu, _context: bpy.context):
    """
    Binds a button or trigger on a UILayout to the BQDMExporter's `invoke()` method.
    Signature follows the requirements for this function to be passed as a draw function to a UI component.

    :param caller: The object containing the layout.
    :param _context: The calling context.
    """

    caller.layout.operator(BQDMExporter.bl_idname, text="BQDM (.bqdm)")


def register():
    "Register the exporter class with Blender and an export option to the export menu"

    bpy.utils.register_class(BQDMExporter)
    TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    "Unregister the exporter class and remove the export option from the export menu"

    bpy.utils.unregister_class(BQDMExporter)
    TOPBAR_MT_file_export.remove(menu_func_export)
