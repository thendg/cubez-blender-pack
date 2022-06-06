# Displacement Baker
> *NOTE: This add-on only bakes procedual displacement set by the material of the object it operates on. It does not bake from the Displace modifier.*

- You should use a math multiplication node instead of "scale" input of the displacement node. this is because any scale set in the node won't get baked out
- Addon expects displacement node as source