# Cubez Packages
A collection of packages developed by the NOIR Development Group for Cubez.io

## TODO
- Write particle converter
- Write procedural sequence baker
  - The procedural sequence baker is an addon which bakes a series of states for some procedural node into a video texture. the resulting video texture can be used in place of the original procedural texture, saving on processing and helping with export preparation. This difference between this and the procedural displacement baker is that the pdb is designed specfically for baking displacement of an object. this does not replace the pdb because the pdb is still better for displacement baking since it doesn't rely on videos so will require less memory for runtime engines.
  - for gltf target platforms, it should only be used when reallly needed because it is very costly for renderers to use video textures at runtime
- [ ] Finish writing READMEs
  - [ ] and `src/dev` documentation
- Convert documentation to Google Style
- Implement `mypy`
  - precommit hook?
- [ ] Write particle converter (`./particle_converter`)
  - [ ] Emission
  - [ ] Hair


## Notes
- `src/dev` could be released as a free package for developers