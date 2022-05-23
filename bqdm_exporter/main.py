import bpy
import os

IMAGE_SIZE = 4096
IMAGE_FORMAT = "PNG"
SEQUENCE_DIR = "./sequence"

img = bpy.data.images.new("BakeTarget", width=IMAGE_SIZE, height=IMAGE_SIZE)
img.file_format = IMAGE_FORMAT

for seq_no, frame in enumerate(
    range(bpy.context.scene.frame_start, bpy.context.scene.frame_start + 1)
):
    bpy.context.scene.frame_set(frame)
    bpy.ops.object.bake()
    img.filepath = os.path.join(
        os.path.abspath(SEQUENCE_DIR), str(seq_no).zfill(4) + f".{IMAGE_FORMAT.lower()}"
    )
    img.save()
