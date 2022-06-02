import glob
import os
import sys
from zipfile import ZipFile

sys.path += [os.path.abspath(os.path.dirname(__file__))]

from argparser import Argparser


def bundle(
    include: list[str],
    exclude: list[str] = [],
    overwrite: bool = True,
    src: str = ".",
    output: str = ".",
    arcname: str = ".",
) -> None:
    """
    Bundle the source files of this repository into a zip archive.

    :param include: A list of file extensions to include in the archive. Should not include the `.` prefix.
    :param exclude: A list of filenames to exclude from the archive realtive to the source folder. (Can be glob pattern but do not include the `!**/` prefix)
    :param overwrite: Should be `True` if the function should overwrite an exist bundle, `False` otherwise.
    :param src: The path to the source code.
    :param output: The directory to build the bundle to.
    :param arcname: The name of the bundle.
    """

    os.chdir(src)

    # Delete old bundle
    build_path = os.path.join(output, f"{arcname}.zip")
    if os.path.exists(build_path):
        if not overwrite:
            return
        os.remove(build_path)
    else:
        os.makedirs(output, exist_ok=True)

    # Get excluded files
    excluded = []
    for e in exclude:
        excluded += glob.glob(f"**/{e}", recursive=True)

    # Create archive
    with ZipFile(build_path, "w") as bundle:
        for ext in include:
            for file in glob.glob(f"**/*.{ext}", recursive=True):
                if file not in excluded:
                    bundle.write(file, arcname=os.path.join(arcname, file))


if __name__ == "__main__":
    ################
    # Bundle addon #
    ################

    parser = Argparser(
        opts=["include", "exclude", "src", "output", "arcname"],
        flags=["overwrite", "build"],
    )
    parser.parse(sys.argv)
    output = os.path.abspath(parser.get("output"))
    arcname = parser.get("arcname")

    bundle(
        parser.get("include").split(","),
        exclude=parser.get("exclude").split(","),
        src=parser.get("src"),
        output=output,
        arcname=arcname,
    )

    if parser.get("build"):
        print(f'Built to "{os.path.join(output, arcname)}".')
    else:
        ######################################
        # Update and enable addon in Blender #
        ######################################

        import bpy

        # Calling addon_remove() attempts a GUI redraw, which breaks because it is being called
        # from outside of an operator so we just catch the error that it raises
        try:
            # We have to use addon_remove() because calling addon_install(overwrite=True) doesn't
            # delete old files from the addon, so we have to delete the whole addon and reinstall
            bpy.ops.preferences.addon_disable(module=arcname)
            bpy.ops.preferences.addon_remove(module=arcname)
        except:
            pass

        bpy.ops.preferences.addon_install(filepath=os.path.join(output, arcname))
        bpy.ops.preferences.addon_enable(module=arcname)

        print("\n############ LOAD SUCCESSFUL ############")
