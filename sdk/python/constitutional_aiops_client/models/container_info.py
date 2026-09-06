from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ContainerInfo")


@_attrs_define
class ContainerInfo:
    """Container information.

    Attributes:
        name (str):
        service (str):
        status (str): running, stopped, restarting, exited
        description (None | str | Unset):
        health (None | str | Unset): healthy, unhealthy, starting, none
        image (None | str | Unset):
        monitored (bool | Unset):  Default: False.
        port (None | str | Unset):
    """

    name: str
    service: str
    status: str
    description: None | str | Unset = UNSET
    health: None | str | Unset = UNSET
    image: None | str | Unset = UNSET
    monitored: bool | Unset = False
    port: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        service = self.service

        status = self.status

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        health: None | str | Unset
        if isinstance(self.health, Unset):
            health = UNSET
        else:
            health = self.health

        image: None | str | Unset
        if isinstance(self.image, Unset):
            image = UNSET
        else:
            image = self.image

        monitored = self.monitored

        port: None | str | Unset
        if isinstance(self.port, Unset):
            port = UNSET
        else:
            port = self.port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "service": service,
                "status": status,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if health is not UNSET:
            field_dict["health"] = health
        if image is not UNSET:
            field_dict["image"] = image
        if monitored is not UNSET:
            field_dict["monitored"] = monitored
        if port is not UNSET:
            field_dict["port"] = port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        service = d.pop("service")

        status = d.pop("status")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_health(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        health = _parse_health(d.pop("health", UNSET))

        def _parse_image(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        image = _parse_image(d.pop("image", UNSET))

        monitored = d.pop("monitored", UNSET)

        def _parse_port(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        port = _parse_port(d.pop("port", UNSET))

        container_info = cls(
            name=name,
            service=service,
            status=status,
            description=description,
            health=health,
            image=image,
            monitored=monitored,
            port=port,
        )

        container_info.additional_properties = d
        return container_info

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
