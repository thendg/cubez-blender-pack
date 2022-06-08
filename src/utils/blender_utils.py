from typing import Iterable, Optional, cast

import bpy
from bpy.types import Collection, Key, Mesh, Node, NodeLink, NodeTree, Object
from . import common_utils


def copy_collection(src: Collection, dest: Collection, suffix="copy") -> None:
    """
    Recursively copy the contents of the collection src into the collection dest.

    :param src: The collection to copy from.
    :param dest: The collection to copy to.
    :param prefix: A string to suffix the names of copied collections and objects with.
    """

    for obj in cast(Iterable[Object], src.objects):
        obj_dup: Object = obj.copy()
        obj_dup.data = obj.data.copy()
        obj_dup.name = common_utils.apply_suffix(obj.name, suffix)
        dest.objects.link(obj_dup)

    for coll in cast(Iterable[Collection], src.children):
        coll_dup = bpy.data.collections.new(
            common_utils.apply_suffix(coll.name, suffix)
        )
        dest.children.link(coll_dup)
        copy_collection(coll, coll_dup, suffix)


def get_node_of_type(tree: NodeTree, type: str) -> Optional[Node]:
    """
    Get the first node with type `type` from the node tree `tree`.

    :param tree: The tree to search
    :param type: The node type to search for
    :returns: the first node in `tree` with the type `type`, or None if no nodes with the given type could be found
    """

    for node in cast(Iterable[Node], tree.nodes):
        if node.type == type:
            return node
    return None


def get_link(node: Node, socket_name: str, output: bool = False) -> Optional[NodeLink]:
    """
    Get the first link from a socket.

    :param node: The node containing the socket.
    :param socket_name: The name of the socket.
    :param output: Should be True if the desired socket is an output socket, False otherwise
    """
    sockets = node.outputs if output else node.inputs
    links: tuple[NodeLink] = sockets[socket_name].links
    if links:
        return links[0]
    else:
        return None


def find_shape_key_container(obj: Object) -> Optional[Key]:
    """
    Search `bpy.data.shape_keys` to find the Key object containing the Shape Keys for a given object

    :param current: The object who's Shape Keys are being searched for.
    :returns: the Key object if it was found, `None` otherwise.
    """

    for shape_key_container in cast(Iterable[Key], bpy.data.shape_keys):
        if shape_key_container.user == obj.data:
            return shape_key_container
    return None


def check_obj(obj: Object):
    """
    Check that an objet has the correct prerequisites for material processing, report an error otherwise. The objext is considered invalid if:
    - It has no UV map
    - It has no active material
    - The active material of the object has no "Material Output" node
    - The active material of the object has an empty "Surface" input for it's "Material Output" node

    :param obj: The object to check.
    :raises RuntimeError: if the object is invalid.
    """

    # Check UV Map
    mesh: Mesh = obj.data
    if not mesh.uv_layers:
        raise RuntimeError(f'Mesh "{mesh.name}" has no UV map.')

    # Check active material
    if not obj.active_material:
        raise RuntimeError(f'Object "{obj.name}" has no active material.')

    mat_tree = obj.active_material.node_tree
    output_node = get_node_of_type(mat_tree, "OUTPUT_MATERIAL")

    # Check Material Output node
    if not output_node:
        raise RuntimeError(
            f'Active material of the object "{obj.name}" has no Material Output node.'
        )

    # Check Surface input for Material Output node
    if not get_link(output_node, "Surface").from_socket:
        raise RuntimeError(
            f'Active material of the object "{obj.name}" has no surface input.'
        )
