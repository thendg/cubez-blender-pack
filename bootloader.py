from distutils.command.build import build
import os
import glob
import sys
from zipfile import ZipFile


def get_build_path() -> str:
    """
    Returns the path to the build file.
    """
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "build",
        "CubezBlenderPack.zip",
    )


def bundle(
    include: list[str] = ["py"], exclude: list[str] = [], overwrite: bool = True
) -> None:
    """
    Bundle the source files of this repository into a zip archive.

    :param include: A list of file extensions to include in the archive. Should not include the `.` prefix.
    :param exclude: A list of filenames to exclude from the archive. (Can be glob pattern but do not include the `!**/` prefix)
    :param overwrite: Should be `True` if the function should overwrite an exist bundle, `False` otherwise.
    """

    build_path = get_build_path()
    if os.path.exists(build_path):
        if not overwrite:
            return
        os.remove(build_path)

    excluded = []
    for e in exclude:
        excluded += glob.glob(f"**/{e}", recursive=True)

    with ZipFile(build_path, "w") as zipf:
        for ext in include:
            for build_path in glob.glob(f"**/*.{ext}", recursive=True):
                if build_path not in excluded:
                    zipf.write(build_path)


if __name__ == "__main__":
    bundle(exclude=["bootloader.py", "launch.py"])
    if "--build" in sys.argv:
        print(f'Built to "{get_build_path()}".')
    else:
        import bpy

        bpy.ops.preferences.addon_install(filepath=get_build_path())
