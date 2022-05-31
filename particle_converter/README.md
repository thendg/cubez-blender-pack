# Particle Converter

## Notes
- To bake static emission particle systems and all hair particle systems, we:
  - Use convert to mesh from modifer
  - Apply material
  - For hair:
    - Merge verts b distance
    - Convert to curve
    - Apply bevel with depth 0.0007
    - Convert to mesh
    - Unwrap mesh with "UV > Unwrap" auto unwrapping
    - Apply material
- We can convert instanced emission particles using `convert_emission_particle.py`. The script is ready to be pasted straight into addon code
- We can't convert animated hair, all hair conversions will be static meshes representing the state of the emitter for the frame
  they are converted.