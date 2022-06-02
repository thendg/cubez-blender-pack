import glob
import os
import sys
from zipfile import ZipFile

ARCHIVE_NAME = "cubez-blender-pack"


def bundle(
    include: list[str],
    exclude: list[str] = [],
    overwrite: bool = True,
    output: str = ".",
) -> None:
    """
    Bundle the source files of this repository into a zip archive.

    :param include: A list of file extensions to include in the archive. Should not include the `.` prefix.
    :param exclude: A list of filenames to exclude from the archive. (Can be glob pattern but do not include the `!**/` prefix)
    :param overwrite: Should be `True` if the function should overwrite an exist bundle, `False` otherwise.
    :param output: The path to build the bundle to.
    """

    if os.path.exists(output):
        if not overwrite:
            return
        os.remove(output)

    excluded = []
    for e in exclude:
        excluded += glob.glob(f"**/{e}", recursive=True)

    with ZipFile(output, "w") as archive:
        for ext in include:
            for file in glob.glob(f"**/*.{ext}", recursive=True):
                if file not in excluded:
                    archive.write(file, arcname=os.path.join(ARCHIVE_NAME, file))


if __name__ == "__main__":
    build_path = os.path.join(
        os.getcwd(),
        "build",
        f"{ARCHIVE_NAME}.zip",
    )

    bundle(["py"], exclude=["dev/*"], output=build_path)
    if "--build" in sys.argv:
        print(f'Built to "{build_path}".')
    else:
        import bpy

        bpy.ops.preferences.addon_remove(module=ARCHIVE_NAME)
        bpy.ops.preferences.addon_install(filepath=build_path)
        bpy.ops.preferences.addon_enable(module=ARCHIVE_NAME)
