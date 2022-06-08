from typing import Iterable, Optional, cast

import bpy
from bpy.types import Collection, Key, Node, NodeLink, NodeTree, Object
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
