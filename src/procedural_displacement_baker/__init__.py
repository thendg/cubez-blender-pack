from typing import Type

# Order is important
from .properties import PDBProperties
from .operator import PDBOperator
from .panel import PDBPanel


def get_classes() -> tuple[Type]:
    return (
        PDBProperties,
        PDBOperator,
        PDBPanel,
    )
