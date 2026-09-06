from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ModelsTestResult")


@_attrs_define
class ModelsTestResult:
    """Per-agent liveness result for the 'Test connection' button.

    Attributes:
        fast_agent (bool):
        reasoning_agent (bool):
    """

    fast_agent: bool
    reasoning_agent: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fast_agent = self.fast_agent

        reasoning_agent = self.reasoning_agent

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "fast_agent": fast_agent,
                "reasoning_agent": reasoning_agent,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        fast_agent = d.pop("fast_agent")

        reasoning_agent = d.pop("reasoning_agent")

        models_test_result = cls(
            fast_agent=fast_agent,
            reasoning_agent=reasoning_agent,
        )

        models_test_result.additional_properties = d
        return models_test_result

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
