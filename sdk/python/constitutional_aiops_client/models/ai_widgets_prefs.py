from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AiWidgetsPrefs")


@_attrs_define
class AiWidgetsPrefs:
    """The per-user opt-in state for the LLM insight widgets.

    Attributes:
        auto_explain (bool | Unset):  Default: False.
        enabled (bool | Unset):  Default: False.
    """

    auto_explain: bool | Unset = False
    enabled: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_explain = self.auto_explain

        enabled = self.enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if auto_explain is not UNSET:
            field_dict["autoExplain"] = auto_explain
        if enabled is not UNSET:
            field_dict["enabled"] = enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        auto_explain = d.pop("autoExplain", UNSET)

        enabled = d.pop("enabled", UNSET)

        ai_widgets_prefs = cls(
            auto_explain=auto_explain,
            enabled=enabled,
        )

        ai_widgets_prefs.additional_properties = d
        return ai_widgets_prefs

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
