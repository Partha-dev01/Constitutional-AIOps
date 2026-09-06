from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.remote_host import RemoteHost


T = TypeVar("T", bound="RemoteHostsResponse")


@_attrs_define
class RemoteHostsResponse:
    """Response containing all known remote/edge hosts.

    Attributes:
        hosts (list[RemoteHost]):
        source (str): Which telemetry store was queried: prometheus, loki, both, or none
        total (int):
    """

    hosts: list[RemoteHost]
    source: str
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hosts = []
        for hosts_item_data in self.hosts:
            hosts_item = hosts_item_data.to_dict()
            hosts.append(hosts_item)

        source = self.source

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hosts": hosts,
                "source": source,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.remote_host import RemoteHost  # noqa: PLC0415

        d = dict(src_dict)
        hosts = []
        _hosts = d.pop("hosts")
        for hosts_item_data in _hosts:
            hosts_item = RemoteHost.from_dict(hosts_item_data)

            hosts.append(hosts_item)

        source = d.pop("source")

        total = d.pop("total")

        remote_hosts_response = cls(
            hosts=hosts,
            source=source,
            total=total,
        )

        remote_hosts_response.additional_properties = d
        return remote_hosts_response

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
