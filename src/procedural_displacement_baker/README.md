# Displacement Baker
An addon for baking procedural material displacement into static displacement texture maps. This addon will bake a single frame of procedural material displacement (static displacement) into a displacement map which is used as the source for an image texture, applied to a "Displace" modifier on the object. For a series of frames of procedural material displacement (animated displacement), the same process is applied for each frame in the timeline, each Displace modifier is applied as a shape key. The shape key is keyframed to only be active for the current frame, then the process repeats for the next frame.

Applying the addon will disable the material displacement of the object.

> *NOTE: This add-on only bakes procedual displacement set by the material of the object it operates on. It does not bake from the Displace modifier.*

## Usage Notes
- The addon expects a "Displacement" node as the input node for the displacement input of the "Material Ouptut" node. If you material is not setup like this, the baker will likely not work or produce unexpected results.
- You should use a "Math" node in "Multiply" mode instead of using the "Scale" input of the displacement node. This exposes the scaling of the source height map outside of the displacement node, allowing the resulting height map to get baked. When the height map is scaled *within* the displacement node, the resulting computation **cannot** be baked into a map, so won't be applied to the object.
- Running the addon, may leave behind some unused datablocks generated during the export. These can be removed by "File > Cleanup > ...", *however*, this can remove **all** unused datablocks in from your `.blend` file, including unused datablocks that you created, so be sure that you won't lose anything you need.
    > *This is why the add-on doesn't perform the cleanup automatically.*