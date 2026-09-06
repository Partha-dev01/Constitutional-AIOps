from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RemoteHost")


@_attrs_define
class RemoteHost:
    """Remote/edge host monitored via Grafana Alloy edge agent.

    Attributes:
        edge_label (str): The 'edge' label value set in the agent .env
        status (str): up, down, or unknown
        last_seen (None | str | Unset): ISO timestamp of most recent metric/log activity
        recent_log_lines (int | Unset): Log lines seen in Loki in the last 15 minutes (0 = no data or Loki unreachable)
            Default: 0.
        targets_total (int | Unset): Total Prometheus scrape targets seen Default: 0.
        targets_up (int | Unset): Number of Prometheus scrape targets reporting up=1 Default: 0.
    """

    edge_label: str
    status: str
    last_seen: None | str | Unset = UNSET
    recent_log_lines: int | Unset = 0
    targets_total: int | Unset = 0
    targets_up: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        edge_label = self.edge_label

        status = self.status

        last_seen: None | str | Unset
        if isinstance(self.last_seen, Unset):
            last_seen = UNSET
        else:
            last_seen = self.last_seen

        recent_log_lines = self.recent_log_lines

        targets_total = self.targets_total

        targets_up = self.targets_up

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "edge_label": edge_label,
                "status": status,
            }
        )
        if last_seen is not UNSET:
            field_dict["last_seen"] = last_seen
        if recent_log_lines is not UNSET:
            field_dict["recent_log_lines"] = recent_log_lines
        if targets_total is not UNSET:
            field_dict["targets_total"] = targets_total
        if targets_up is not UNSET:
            field_dict["targets_up"] = targets_up

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        edge_label = d.pop("edge_label")

        status = d.pop("status")

        def _parse_last_seen(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_seen = _parse_last_seen(d.pop("last_seen", UNSET))

        recent_log_lines = d.pop("recent_log_lines", UNSET)

        targets_total = d.pop("targets_total", UNSET)

        targets_up = d.pop("targets_up", UNSET)

        remote_host = cls(
            edge_label=edge_label,
            status=status,
            last_seen=last_seen,
            recent_log_lines=recent_log_lines,
            targets_total=targets_total,
            targets_up=targets_up,
        )

        remote_host.additional_properties = d
        return remote_host

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
