# Material Marshall
An addon to prepare materials for glTF export. Materials can be marshalled into the following structures in preparation for glTF export:
- Metallic/Roughness PBR
- Shadless Diffuse Map

- user can bake the *entire* material into a single diffuse texture, which will be exposed to gltf as a shadless texture.
  - minimal processing and storage at runtime
  - diffuse texture should go into a background node so they will be interpreted as "unlit" (shadeless)
  - diffuse texture should get post processed but PBR textures should not

## Usage Notes
- Make sure all your textures use their objects' UV coordinate maps. When textures are baked, the resulting baked images will be applied to objects by their UV, so creating your textures around their UV maps ensures the most consistent and predictable results.
  > *NOTE: These UV maps should be finalised. Any modifiers that introduce geometry should already be applied, since they will affect the UV map. Ideally, you should apply these modifiers before UV unwrapping your objects.*

## Model
Use `.glb`
Use Draco compression

## Notes
- Materials should be post-processed
- Texture sizes are 256px, 512px, 1024px, 2048px, 4096px, 8192px squares. Using the bounding box of each object, we determine the minumum sized texture it will have. We then bake textures at this texture, and the next three sizes above it, to create low, standard and high resolutions appropriate for each object.
- we cant export `.ktx2` directly out of blender, so we'll have to export something else, then convert that into `.ktx2`. The format we export out of blender should be whatever produces the best looking and smallest result after `.ktx2` compression
  - https://github.khronos.org/KTX-Software/ktxtools/toktx.html
  - https://github.com/BinomialLLC/basis_universal
    - This has automatic Zstandard compression compression for `.ktx2`
  - we should create textures with mipmaps. even though this will make the files bigger, THREE will generate mipmaps anyway so the GPU will still end up storing them. considering this, we might aswell generate them in advance to improve runtime load speed.
- the only reason we're not using video texture instead of texture sets is because with images we can compress each one as `.ktx2` but we cant do that with video? If we can find a good GPU video compression format then this is the better way to go. The base state texture will still be a `.ktx2`. If runtime image swapping is slow, we'll be forced to swap to compressed MP4 video textures
- How do we support cameras?
  - Like sketchfab does
- How will we add support for 2D digital art?
- https://www.khronos.org/blog/using-the-new-gltf-extensions-volume-index-of-refraction-and-specular