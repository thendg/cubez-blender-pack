import os
import subprocess
import sys

from argparser import Argparser

if __name__ == "__main__":
    parser = Argparser(opts=["blender"])
    parser.parse(sys.argv)

    args = [
        parser.get("blender"),
        "--python",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "bootloader.py"),
        "--",
        "./src",
    ]
    print(args)
    subprocess.run(args)
