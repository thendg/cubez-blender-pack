# Material Marshall
An addon to prepare materials for glTF export. Materials can be marshalled into the following structures in preparation for glTF export:
- Metallic/Roughness PBR Materials
- Shadless Diffuse Materials

The Metallic/Roughness PBR Materials are Physically Based Rendering materials utilising the Metallic/Roughness workflow (as opposed to the Specular/Glossiness workflow). These are realtime materials which calculate the interaction and appearance of a mesh surface in it's surrounding environment at runtime. Shadless Diffuse Materials are fully baked static textures, applied to a mesh surface describing the final appearance of an object. In comparison, Metallic/Roughness PBR Materials describe *how* an object should look (declarative) while Shadless Diffuse Materials describe *what* an object looks like (imperative).

Since Shadless Diffuse Materials are imperative descriptions of appearance, they are much cheaper to compute since they don't require any runtime calculation. Because of this, it is recommended to use Shadeless diffuse maps *whereever possible*. This minimises the sizes of your materials, optimising storage and makes the model easier to compute for clients, improving overall perfomance. For static scenes this works perfectly, however, it doesn't work as well when we start to introduce moving elements. Animated scenes contain moving objects. If aon object moves, any surface refractions, casted shadows or received shadows relative to the object should change. For Shadless Diffuse Materials, this would not be the case since everything is precalculated and baked into a single texture, so in this situation a Metallic/Roughness PBR Material would be required since there are elements of the scene which would need to be calculated at runtime.
> *NOTE: This doesn't mean that the **entire** scene must use Metallic/Roughness PBR Materials, only the elements which are affected by animation.*

Other reasons that can influence you choice of material structure include:
- **Lighting:** Lighting is often calculated much more accruately by ray-traced rendering engines than realtime engines so if you prefer the way your lighting looks you may want to prebake your lighting using a Shadless Diffuse Material. This goes for lighting *effects* too, for example if your material change appearance depending on the camera's angle to the surface.
- **Sylistic Choices:** With certain art styles (like "hand drawn" or "cartoon" styles), it may be undesirable to describe your material declaratively - leaving the runtime engine to do the calculations on how it should look. If a certain material needs to look a specific way, a Shadless Diffuse Material is the way to go.
- **Material Properties:** There are some types of material, like transmissive materials for example, which **must** be calculated at runtime, in which case there is no option other than a Metallic/Roughness PBR Material. This is due to contraints on the capabilities of ray-traced rendering engines. For the given example, the results of tranmission cannot be baked into a texture since the appearance of a tranmissive texture requires the runtime capabilities of the ray-traced engines to render. This is why attempting to bake tranmissive materials always yeilds strange results. The same goes for other material aspects like transparency, translucency, reflection and refraction of glass-like materials, with some aspects looking better/worse when baked than others.

## Usage Notes
- Make sure all your textures use their objects' UV coordinate maps. When textures are baked, the resulting baked images will be applied to objects by their UV, so creating your textures around their UV maps ensures the most consistent and predictable results.
  > *NOTE: These UV maps should be finalised. Any modifiers that introduce geometry should already be applied, since they will affect the UV map. Ideally, you should apply these modifiers before UV unwrapping your objects.*
- Transparency is used to represent parts of a mesh which aren't visible, for example the holes in a fishing net. Transparency **should not** be used for gradurally blending/fading out materials but instead as a binary property defining if a part of a mesh is or is not visible. As such, all marshalled materials use the "Alpha Clip" blend mode. To achieve gradual fades in visibility, utilise a material's tranmissive properties.

# Notes
- if we're gonna do the multiple size export, we need to know how to store the textures now because this is the point when they get baked so we need to know how to bake them (size wise).
  - If we use [KHR_materials_variants](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_materials_variants) extension, we can store the different textures as "variants"
- pbr structure:
  - ORM map
  - Normal map (tangent space)
  - emission
  - backface culling
  - blend mode: alpha clip.
    - (alpha clip recommended but then you can't have gradient alpha)
- base color should be sRGB, everything else shoudl be non-color
- both mat types will use UV map. We won't support UV transforms because of the complications:
  > *"UV transforms are supported, with several key limitations. Transforms applied to a texture using the first UV slot (that is, any texture except the ambient occlusion map and light map) must share the same transform, or no transform at all. The ambient occlusion map and light map textures cannot be transformed. No more than one transform may be used per material."*
  >
  > *From [threejs.org](https://threejs.org/docs/?q=gltf#examples/en/loaders/GLTFLoader).*
