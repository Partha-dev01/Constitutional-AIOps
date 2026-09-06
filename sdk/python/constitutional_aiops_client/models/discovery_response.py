from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.discovered_container import DiscoveredContainer


T = TypeVar("T", bound="DiscoveryResponse")


@_attrs_define
class DiscoveryResponse:
    """Container discovery response.

    Attributes:
        containers (list[DiscoveredContainer]):
        total (int):
    """

    containers: list[DiscoveredContainer]
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        containers = []
        for containers_item_data in self.containers:
            containers_item = containers_item_data.to_dict()
            containers.append(containers_item)

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "containers": containers,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.discovered_container import DiscoveredContainer  # noqa: PLC0415

        d = dict(src_dict)
        containers = []
        _containers = d.pop("containers")
        for containers_item_data in _containers:
            containers_item = DiscoveredContainer.from_dict(containers_item_data)

            containers.append(containers_item)

        total = d.pop("total")

        discovery_response = cls(
            containers=containers,
            total=total,
        )

        discovery_response.additional_properties = d
        return discovery_response

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
