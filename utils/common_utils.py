from typing import Any, Callable, Iterable, Optional, TypeVar

T = TypeVar("T")


def apply_suffix(s: Any, suffix: Any) -> str:
    """
    Apply a suffix to a string. Arguments are casted to their string form.

    :param s: The string to suffix.
    :param suffix: The suffix to apply.
    """

    return f"{str(s)}-{str(suffix)}"


def search(
    current: T, is_target: Callable[[T], bool], get_children: Callable[[T], Iterable[T]]
) -> Optional[T]:
    """
    Recursively search a tree-like collection of type `T` for an element of type `T`.

    :param current: The current node being searched.
    :param is_target: A predicate function that returns True when passed the desired element.
    :param gen: A function that returns the direct children of a node when passed a node. The children should be returned as an iterable. This function should not return indirect descendants.
    :returns: the target if it was found, `None` otherwise.
    """

    found = None
    if is_target(current):
        return current
    for item in get_children(current):
        found = search(item, is_target, get_children)
        if found:
            return found
    return found
