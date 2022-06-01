import os
import glob
from zipfile import ZipFile

EXTS = ["py"]


def get_build_path() -> str:
    """
    Returns the path to the build file
    """

    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "build",
        "Cubez Blender Pack.zip",
    )
    if os.path.exists(path):
        os.remove(path)
    return path


build_path = get_build_path()
print(build_path)
with ZipFile(build_path, "w") as zipf:
    for ext in EXTS:
        for path in glob.glob(f"**/*.{ext}", recursive=True):
            zipf.write(path)
