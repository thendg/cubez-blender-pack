import atexit
import glob
import os
import shutil
import sys
from zipfile import ZipFile

sys.path += [os.path.abspath(os.path.dirname(__file__))]

from argparser import Argparser


def get_build_path(output: str, arcname: str) -> str:
    """
    Construct a build path from an ouput folder path and archive name.

    :param ouptut: The output folder path.
    :param arcname: The archive name
    """

    return os.path.join(output, f"{arcname}.zip")


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
    build_path = get_build_path(output, arcname)
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
    print("\nBOOTLOADING...")

    ################
    # Bundle addon #
    ################

    parser = Argparser(
        opts=["include", "exclude", "src", "output", "name"],
        flags=["overwrite", "build"],
    )
    parser.parse(sys.argv)
    output = os.path.abspath(parser.get("output"))
    name = parser.get("name")
    build_path = get_build_path(output, name)

    bundle(
        parser.get("include").split(","),
        exclude=parser.get("exclude").split(","),
        overwrite=parser.getf("overwrite"),
        src=parser.get("src"),
        output=output,
        arcname=name,
    )
    print(f'Bundle built to "{build_path}".\n')

    if not parser.getf("build"):
        ######################################
        # Update and enable addon in Blender #
        ######################################

        import bpy
        import addon_utils

        bpy.ops.preferences.addon_install(filepath=build_path)
        bpy.ops.preferences.addon_enable(module=name)

        modpath: str = None
        for mod in addon_utils.modules():
            if mod.__name__ == name:
                modpath = mod.__file__
                break

        atexit.register(lambda path: shutil.rmtree(os.path.dirname(path)), modpath)

        print("\n############ LOAD SUCCESSFUL ############\n")
