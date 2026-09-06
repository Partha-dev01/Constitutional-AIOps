from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DiscoveredContainer")


@_attrs_define
class DiscoveredContainer:
    """Discovered container from Docker.

    Attributes:
        created (None | str):
        image (str):
        monitored (bool):
        name (str):
        ports (None | str):
        status (str):
    """

    created: None | str
    image: str
    monitored: bool
    name: str
    ports: None | str
    status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created: None | str
        created = self.created

        image = self.image

        monitored = self.monitored

        name = self.name

        ports: None | str
        ports = self.ports

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "created": created,
                "image": image,
                "monitored": monitored,
                "name": name,
                "ports": ports,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_created(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        created = _parse_created(d.pop("created"))

        image = d.pop("image")

        monitored = d.pop("monitored")

        name = d.pop("name")

        def _parse_ports(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        ports = _parse_ports(d.pop("ports"))

        status = d.pop("status")

        discovered_container = cls(
            created=created,
            image=image,
            monitored=monitored,
            name=name,
            ports=ports,
            status=status,
        )

        discovered_container.additional_properties = d
        return discovered_container

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
