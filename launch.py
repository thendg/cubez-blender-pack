import subprocess
import os

BLENDER = "C:\\Program Files\\Blender Foundation\\Blender 3.1\\blender.exe"

if __name__ == "__main__":
    args = [BLENDER, "--python", os.path.abspath("bootloader.py")]
    print(args)
    subprocess.run(args)
