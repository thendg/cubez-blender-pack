# Development Scripts
> *NOTE:* These scripts should be run from the root directory of the project, **not** from `./dev`.

## `launch.py`
This script can be run to execute blender with the "Cubez Blender Pack" addon installed, updated and activated. The script takes one command line argument: a path pointing to the location of your target Blender installation.

> *The path argument should be escaped on Windows machines*

## `bootloader.py`
This script is responsible for preparing the "Cubez Blender Pack" addon for Blender. It bundles the addon into a `.zip` archive, then installs and activates the addon. If the `--build` flag is present, when this script is invoked, it will bundle the addon and quit (without performing any blender operations). The bundle is placed in a `build` directory, which is placed in the directory that the script was called from.