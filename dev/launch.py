import subprocess
import sys
import os

if __name__ == "__main__":
    args = [
        sys.argv[-1],
        "--python",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "bootloader.py"),
    ]
    print(args)
    subprocess.run(args)
