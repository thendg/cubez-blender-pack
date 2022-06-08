from typing import Type

# Order is important
from .properties import MMProperties
from .operator import MMOperator
from .panel import MMPanel


def get_classes() -> tuple[Type]:
    return (
        MMProperties,
        MMOperator,
        MMPanel,
    )
