from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ReadinessResponse")


@_attrs_define
class ReadinessResponse:
    """Kubernetes readiness probe response.

    Attributes:
        checks_failed (list[str]):
        checks_passed (list[str]):
        ready (bool):
    """

    checks_failed: list[str]
    checks_passed: list[str]
    ready: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        checks_failed = self.checks_failed

        checks_passed = self.checks_passed

        ready = self.ready

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "checks_failed": checks_failed,
                "checks_passed": checks_passed,
                "ready": ready,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        checks_failed = cast(list[str], d.pop("checks_failed"))

        checks_passed = cast(list[str], d.pop("checks_passed"))

        ready = d.pop("ready")

        readiness_response = cls(
            checks_failed=checks_failed,
            checks_passed=checks_passed,
            ready=ready,
        )

        readiness_response.additional_properties = d
        return readiness_response

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
