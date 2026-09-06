from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SeedTopologyResponse")


@_attrs_define
class SeedTopologyResponse:
    """Result of a manual topology seed run.

    Attributes:
        dependencies (int):
        message (str):
        services (int):
        success (bool):
    """

    dependencies: int
    message: str
    services: int
    success: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dependencies = self.dependencies

        message = self.message

        services = self.services

        success = self.success

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dependencies": dependencies,
                "message": message,
                "services": services,
                "success": success,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dependencies = d.pop("dependencies")

        message = d.pop("message")

        services = d.pop("services")

        success = d.pop("success")

        seed_topology_response = cls(
            dependencies=dependencies,
            message=message,
            services=services,
            success=success,
        )

        seed_topology_response.additional_properties = d
        return seed_topology_response

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
