############################################
# Bake particles as aniamted mesh instaces #
############################################

depsgraph = context.evaluated_depsgraph_get()
instance_target = None  # TODO: how to set instance target??

# Iterate all objects to get all active particle systems
for obj in cast(Iterable[Object], context.scene.objects):
    # Create collection for baked particles of this object
    obj_particles_coll = bpy.data.collections.new(name=apply_suffix(obj.name, "PS"))
    # Link new collection to parent collection of object so obj and new collection are siblings
    search(
        context.scene.collection,
        lambda coll: obj.name in coll.objects,
        lambda coll: coll.children,
    ).children.link(obj_particles_coll)
    obj_eval = depsgraph.objects[obj.name]

    # Iterate all particle systems on object
    for i, ps in enumerate(cast(Iterable[ParticleSystem], obj_eval.particle_systems)):
        # Create collection for baked particles of this particle system
        ps_coll = bpy.data.collections.new(
            name=apply_suffix(obj_particles_coll.name, str(i).zfill(3))
        )
        obj_particles_coll.children.link(ps_coll)

        # Create instances of the particle target object for every particle in the particle system.
        instances: list[Object] = []
        for i, _ in cast(Iterable[Particle], ps.particles.extend(ps.child_particles)):
            dup = bpy.data.objects.new(
                name=str(i).zfill(5), object_data=instance_target.data
            )
            ps_coll.objects.link(dup)
            instances.append(dup)

        # Match and keyframe the states instances to the states of their corresponding particles for every frame in the timeline
        for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
            context.scene.frame_set(frame)
            for p, instance in cast(
                tuple[tuple[Particle, Object]], zip(ps.particles, instances)
            ):
                alive = p.alive_state == "ALIVE"
                if alive:
                    instance.scale = (p.size, p.size, p.size)
                else:
                    instance.scale = (0.001, 0.001, 0.001)
                instance.hide_viewport = not alive
                instance.location = p.location
                # Set rotation mode to quaternion to match particle rotation
                instance.rotation_mode = "QUATERNION"
                instance.rotation_quaternion = p.rotation

                instance.keyframe_insert("location")
                instance.keyframe_insert("rotation_quaternion")
                instance.keyframe_insert("scale")
