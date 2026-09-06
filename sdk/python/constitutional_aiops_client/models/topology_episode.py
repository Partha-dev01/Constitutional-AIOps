from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TopologyEpisode")


@_attrs_define
class TopologyEpisode:
    """Recent episode summary attached to a topology node.

    Attributes:
        id (str):
        severity (str): info | warning | error | critical
        title (str):
        at (None | str | Unset): ISO timestamp of detection
    """

    id: str
    severity: str
    title: str
    at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        severity = self.severity

        title = self.title

        at: None | str | Unset
        if isinstance(self.at, Unset):
            at = UNSET
        else:
            at = self.at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "severity": severity,
                "title": title,
            }
        )
        if at is not UNSET:
            field_dict["at"] = at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        severity = d.pop("severity")

        title = d.pop("title")

        def _parse_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        at = _parse_at(d.pop("at", UNSET))

        topology_episode = cls(
            id=id,
            severity=severity,
            title=title,
            at=at,
        )

        topology_episode.additional_properties = d
        return topology_episode

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
