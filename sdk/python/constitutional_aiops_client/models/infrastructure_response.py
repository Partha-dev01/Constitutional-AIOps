from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.container_info import ContainerInfo


T = TypeVar("T", bound="InfrastructureResponse")


@_attrs_define
class InfrastructureResponse:
    """Infrastructure status response.

    Attributes:
        containers (list[ContainerInfo]):
        healthy (int):
        total (int):
        unhealthy (int):
    """

    containers: list[ContainerInfo]
    healthy: int
    total: int
    unhealthy: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        containers = []
        for containers_item_data in self.containers:
            containers_item = containers_item_data.to_dict()
            containers.append(containers_item)

        healthy = self.healthy

        total = self.total

        unhealthy = self.unhealthy

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "containers": containers,
                "healthy": healthy,
                "total": total,
                "unhealthy": unhealthy,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.container_info import ContainerInfo  # noqa: PLC0415

        d = dict(src_dict)
        containers = []
        _containers = d.pop("containers")
        for containers_item_data in _containers:
            containers_item = ContainerInfo.from_dict(containers_item_data)

            containers.append(containers_item)

        healthy = d.pop("healthy")

        total = d.pop("total")

        unhealthy = d.pop("unhealthy")

        infrastructure_response = cls(
            containers=containers,
            healthy=healthy,
            total=total,
            unhealthy=unhealthy,
        )

        infrastructure_response.additional_properties = d
        return infrastructure_response

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
