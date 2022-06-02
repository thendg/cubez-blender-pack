import glob
import os
import sys
from zipfile import ZipFile

ARCHIVE_NAME = "cubez-blender-pack"


def bundle(
    include: list[str],
    exclude: list[str] = [],
    overwrite: bool = True,
    src: str = ".",
    output: str = ".",
) -> None:
    """
    Bundle the source files of this repository into a zip archive.

    :param include: A list of file extensions to include in the archive. Should not include the `.` prefix.
    :param exclude: A list of filenames to exclude from the archive realtive to the source folder. (Can be glob pattern but do not include the `!**/` prefix)
    :param overwrite: Should be `True` if the function should overwrite an exist bundle, `False` otherwise.
    :param src: The path to the source code.
    :param output: The path to build the bundle to.
    """

    os.chdir(src)

    # Delete old bundle
    if os.path.exists(output):
        if not overwrite:
            return
        os.remove(output)
    else:
        os.makedirs(os.path.dirname(output), exist_ok=True)

    # Get excluded files
    excluded = []
    for e in exclude:
        excluded += glob.glob(f"**/{e}", recursive=True)

    # Create archive
    with ZipFile(output, "w") as archive:
        for ext in include:
            for file in glob.glob(f"**/*.{ext}", recursive=True):
                if file not in excluded:
                    archive.write(file, arcname=os.path.join(ARCHIVE_NAME, file))


if __name__ == "__main__":
    ################
    # Bundle addon #
    ################

    build_path = os.path.join(
        os.getcwd(),
        "build",
        f"{ARCHIVE_NAME}.zip",
    )

    bundle(["py"], exclude=["dev/*"], src=sys.argv[-1], output=build_path)

    if "--build" in sys.argv:
        print(f'Built to "{build_path}".')
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
            bpy.ops.preferences.addon_disable(module=ARCHIVE_NAME)
            bpy.ops.preferences.addon_remove(module=ARCHIVE_NAME)
        except:
            pass

        bpy.ops.preferences.addon_install(filepath=build_path)
        bpy.ops.preferences.addon_enable(module=ARCHIVE_NAME)

        print("\n############ LOAD SUCCESSFUL ############")
