import subprocess
import sys
import os

# TODO: make launcher work

if __name__ == "__main__":
    args = [sys.argv[0], "--python", os.path.abspath("bootloader.py")]
    print(args)
    subprocess.run(args)
