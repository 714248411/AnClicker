"""UI-independent instruction parameter description."""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class FieldSpec:
    key: str
    label: str
    kind: str = "text"
    default: Any = ""
    choices: tuple[str, ...] = ()
    required: bool = False
    minimum: float = -1_000_000
    maximum: float = 1_000_000
