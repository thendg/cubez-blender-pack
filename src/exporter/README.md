## Model
Use `.glb`
Use Draco compression

## Notes
- at the moment we are looking at:
  - how we can include as many of the extensions supported [here](https://threejs.org/docs/?q=gltf#examples/en/loaders/GLTFLoader) as possible, and how we can export that data. We can learn to export that data from [here](https://github.com/KhronosGroup/glTF/tree/main/extensions)
  - Blender might have functionality to already export them
  - https://codesandbox.io/s/glass-transmission-enx1u?file=/src/App.js:166-177
  - we need to look at which extensions we actually need and see if blender supports them or if not how we can implement
  - failing this we can forgo the gltf pbr and use custom props to set meshphysicicsmaterial properties

- export lights? especially for realtime materials
- https://docs.blender.org/manual/en/3.1/addons/import_export/scene_gltf2.html#export
- client should allow materials to be post-processed at runtime
- Texture sizes are 256px, 512px, 1024px, 2048px, 4096px, 8192px squares. Using the bounding box of each object, we determine the minumum sized texture it will have. We then bake textures at this texture, and the next three sizes above it, to create low, standard and high resolutions appropriate for each object.
- we cant export `.ktx2` directly out of blender, so we'll have to export something else, then convert that into `.ktx2`. The format we export out of blender should be whatever produces the best looking and smallest result after `.ktx2` compression
  - https://github.khronos.org/KTX-Software/ktxtools/toktx.html
  - https://github.com/BinomialLLC/basis_universal
    - This has automatic Zstandard compression compression for `.ktx2`
  - https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_texture_basisu/README.md#khr_texture_basisu
  - we should create textures with mipmaps. even though this will make the files bigger, THREE will generate mipmaps anyway so the GPU will still end up storing them. considering this, we might aswell generate them in advance to improve runtime load speed.
- How do we support cameras?
  - Static cameras
  - Preanimated cameras
  - Free cameras (you may not want to have a free camera if your scene only looks good from certain angles)
  - Like sketchfab does
- How will we add support for 2D digital art?
