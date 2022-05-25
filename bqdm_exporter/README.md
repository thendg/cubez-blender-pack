# Baked Quasi-Dynamic Material `(.bqdm)` 
The BQDM format describes sets of baked PBR material outputs, and a pipeline for how they are arranged used from render to client. The workflow is used alongside a model described by the glTF 2.0 standard, but creates materials that can be applied to any situation. **Baked Quasi-Dynamic Material** files describe appearance of finalised 3D scenes/models adding support for potential material animation within scenes. **BQDM**s are finalised, so should be treated as an target output media rather than a lossless intermediate/storage format - however, the underlying geometry/material information is retained within the underlying structures of a `.bqdm` file.

## Why?
CG Artists spend hours designing delicate 3D scenes, only to render them into 2D losing an entire dimension of detail. Granted, there aren't many platforms where actual 3D artwork is viewed in 3D - but Cubez.io's sole purpose is to be one of those platforms. When developing Cubez.io, we wanted to be able to view art with all the degrees of freedom the artist had - from every angle and with free camera control around the scene. We also didn't want to comprimise on quality, wanting the textural effects of raytraced rendering engines in real-time. A plain glTF 2.0 would allow us to do some of these things, but used realtime PBR rendering and didn't have the greatest animation support, so BQDM was created to extend the features that we desired.

## Usage
Running in the non-destructive mode, will leave behind some unused datablocks generated during the export. These can be removed by "File > Cleanup > ...", *however*, this can remove **all** unused datablocks in from your `.blend` file, including unused datablocks that you created, so be sure that you won't lose anything you need.
> *This is why the add-on doesn't perform the cleanup automatically.*

Make sure all your textures use their objects' UV coordinate maps. When textures are baked, the resulting baked images will be applied to objects by their UV, so creating your textures around their UV maps ensures the most consistent and predicateble results. Note that these UV maps should be finalised too. Any modifiers that introduce geometry should already be applied, since they will affect the UV map. Ideally, you should apply these modifiers *before* UV unwrapping your objects.

# Technical Specification
## Structure
A single `.bdqm` file is a `gzip` archive consiting of the followng files:
- `model.glb`
- `textures`
- `meta.json`

### Model
`model.glb` is a `draco` compressed glTF Binary file defining the geometric mesh data of the model. This includes:
- Meshes
- Geometry Data
- UV Maps
- Animations
	- *Any supported by Blender's glTF 2.0 exporter*

This glTF, will only contain one scene.

### Textures
`textures` is an directory of `gzip` archives, with each archive containing *"texture sets"* for a single mesh described by the scene in `model.glb`. Each texture set contains the textures that should be applied to the respective mesh while a certain animation is playing, with each individual image in the texture set being the texture to apply for a specific frame of the animation, stored as a `.ktx2` file, compressed with the Basis Universal algorithm in UASTC mode. The root of the directory also contains a texture to apply to the mesh in it's base state. This makes the model **quasi-dynamic**, allowing it to seemingly change in appearance over-time, creating psuedo-dynamic experiences from pre-baked textures. The `textures` directory may look like this:
```
- textures
  -- base.ktx2
  -- sequence1
    -- 0001.ktx2
    -- 0002.ktx2
    -- 0003.ktx2
  -- sequence2
    -- 0001.ktx2
    -- 0002.ktx2
```

## Metadata
Metadata such as version numbers and information about the model are stored in `meta.json`.

## Archiving
Finally, a directory containing `model.glb`, `textures` and `meta.json` is compressed into a `gzip` archive, completing the `bqdm` file.

## Notes
- The exporter expects models to already have UV maps.
- Since the target output is glTF, all displacement will need to be done via displace modifiers so that the modifer can be applied during export, affecting the resulting model. For static displacement, it is up to the artist how they do this - we recommend either plugging a displacement map directly into the texture driving the modifer, or baking a procedurally generated displacement map, and using this to drive the modifer.
- Animated displacement will need to be baked in a similar fashion. We'll generate a displacement map movie texture and use it to drive a displacement modifier on the object. The modifer will be duplicated for each frame in the timeline, with each duplicate referencing a separate frame of the movie texture. Each modifer can then be *"Applied as a Shape"*, generating shape keys for each of the displaced states of the model. These shape keys can then be keyframed, to toggle each state for each frame, then exported in `model.glb`.
- Materials should be post-processed
- Client implemtations should expose options to users to decrease texture swap rate if texture swapping is too expensive (especially at high framerates)
- Texture sizes are 256, 512, 1024, 2048, 4096, 8192 px squares. Using the bounding box of each object, we determine the minumum sized texture it will have. We then bake textures at this texture, and the next three sizes above it, to create low, standard and high resolutions appropriate for each object.
- we cant export `.ktx2` directly out of blender, so we'll have to export something else, then convert that into `.ktx2`. The format we export out of blender should be whatever produces the best looking and smallest result after `.ktx2` compression
  - https://github.khronos.org/KTX-Software/ktxtools/toktx.html
  - https://github.com/BinomialLLC/basis_universal
  - we should create textures with mipmaps. even though this will make the files bigger, THREE will generate mipmaps anyway so the GPU will still end up storing them. considering this, we might aswell generate them in advance to improve runtime load speed.
- the only reason we're not using video texture instead of texture sets is because with images we can compress each one as `.ktx2` but we cant do that with video? If we can find a good GPU video compression format then this is the better way to go. The base state texture will still be a `.ktx2`. If runtime image swapping is slow, we'll be forced to swap to compressed MP4 video textures
- `.ktx2` is only compressed in VRAM, if the textures are taking up too much space in RAM, we can use [Zstandard](https://facebook.github.io/zstd/) to compress them at creation, then expand them at runtime before sending them to the GPU.
- How do we support cameras?
  - Like sketchfab does

## TODO:
- Should we use multires for objects.
  - If we do, who is responsible for it, us or artist?
  - If we do, it will affect baking and glTF exporting
- Implement `mypy`
  - precommit hook?
- Convert documentation to Google Style