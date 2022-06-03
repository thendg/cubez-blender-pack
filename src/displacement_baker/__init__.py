from typing import Type

# Order is important
from .properties import DisplacementBakerProperties
from .operator import DisplacementBakerOperator
from .panel import DisplacementBakerPanel


def get_classes() -> tuple[Type]:
    return (
        DisplacementBakerProperties,
        DisplacementBakerOperator,
        DisplacementBakerPanel,
    )
