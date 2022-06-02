# Geonode Baker

## Notes
- To bake static geonode effects, user can just apply modifier
- To bake animated geonode effects, we can:
  1. Duplicate the object
  2. Apply geonode modifer to duplicate
  3. Join duplicate and original as Shape Key
  4. Increment Frame
  5. Repeat
  - This won't animate any materials though. It will only affect geometry.