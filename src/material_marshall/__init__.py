from typing import Type

from .operator import BQDMExporter


def get_classes() -> tuple[Type]:
    return (BQDMExporter,)
