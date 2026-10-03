"""Normalization helpers for host-provided instruction specifications."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from PySide6.QtGui import QColor

from node_editor.style import DEFAULT_NODE_COLOR


@dataclass(frozen=True, slots=True)
class NodeDisplaySpec:
    """Display metadata required by the palette and node canvas."""

    type_id: str
    title: str
    category: str
    color: QColor


def _read_value(source_, *names_, default=None):
    if isinstance(source_, Mapping):
        for name_ in names_:
            if name_ in source_:
                return source_[name_]
        return default
    for name_ in names_:
        if hasattr(source_, name_):
            return getattr(source_, name_)
    return default


def _make_color(value_) -> QColor:
    color_ = QColor(value_) if value_ is not None else QColor(DEFAULT_NODE_COLOR)
    return color_ if color_.isValid() else QColor(DEFAULT_NODE_COLOR)


def normalize_specs(specs_) -> dict[str, NodeDisplaySpec]:
    """Return specifications keyed by stable instruction type id.

    ``specs_`` may be a mapping keyed by type id, or an iterable of mappings /
    objects containing ``type_id``.  Chinese field aliases are accepted so the
    component can consume the current Clicker registry without an adapter.
    """

    if specs_ is None:
        return {}

    if isinstance(specs_, Mapping):
        entries_ = specs_.items()
    elif isinstance(specs_, Iterable) and not isinstance(specs_, (str, bytes)):
        entries_ = ((None, entry_) for entry_ in specs_)
    else:
        raise TypeError("specs must be a mapping or iterable")

    normalized_: dict[str, NodeDisplaySpec] = {}
    for key_, raw_spec_ in entries_:
        type_value_ = key_ if key_ is not None else _read_value(
            raw_spec_, "type_id", "id", "指令类型"
        )
        if type_value_ is None or str(type_value_).strip() == "":
            raise ValueError("instruction spec is missing type_id")
        type_id_ = str(type_value_)
        title_ = str(
            _read_value(
                raw_spec_, "title", "name", "display_name", "名称", default=type_id_
            )
        )
        category_ = str(
            _read_value(raw_spec_, "category", "group", "分类", default="其他")
        )
        color_ = _make_color(
            _read_value(raw_spec_, "color", "node_color", "颜色")
        )
        normalized_[type_id_] = NodeDisplaySpec(type_id_, title_, category_, color_)
    return normalized_
