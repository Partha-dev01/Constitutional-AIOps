from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ChaosActionResponse")


@_attrs_define
class ChaosActionResponse:
    """Result of a chaos start/heal call.

    Attributes:
        action (str):
        detail (str):
        scenario (str):
        success (bool):
    """

    action: str
    detail: str
    scenario: str
    success: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        detail = self.detail

        scenario = self.scenario

        success = self.success

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action": action,
                "detail": detail,
                "scenario": scenario,
                "success": success,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = d.pop("action")

        detail = d.pop("detail")

        scenario = d.pop("scenario")

        success = d.pop("success")

        chaos_action_response = cls(
            action=action,
            detail=detail,
            scenario=scenario,
            success=success,
        )

        chaos_action_response.additional_properties = d
        return chaos_action_response

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
