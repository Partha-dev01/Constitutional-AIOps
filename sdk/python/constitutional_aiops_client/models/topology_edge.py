from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TopologyEdge")


@_attrs_define
class TopologyEdge:
    """A dependency or telemetry-shipping link in the schema graph.

    Attributes:
        buckets (list[int]): Per-bucket co-episode counts, oldest → newest
        id (str): "source->target"
        kind (str): static | dynamic
        relationship (str): DEPENDS_ON | SHIPS_TELEMETRY
        source (str):
        target (str):
        co_episode_count (int | Unset):  Default: 0.
    """

    buckets: list[int]
    id: str
    kind: str
    relationship: str
    source: str
    target: str
    co_episode_count: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        buckets = self.buckets

        id = self.id

        kind = self.kind

        relationship = self.relationship

        source = self.source

        target = self.target

        co_episode_count = self.co_episode_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "buckets": buckets,
                "id": id,
                "kind": kind,
                "relationship": relationship,
                "source": source,
                "target": target,
            }
        )
        if co_episode_count is not UNSET:
            field_dict["co_episode_count"] = co_episode_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        buckets = cast(list[int], d.pop("buckets"))

        id = d.pop("id")

        kind = d.pop("kind")

        relationship = d.pop("relationship")

        source = d.pop("source")

        target = d.pop("target")

        co_episode_count = d.pop("co_episode_count", UNSET)

        topology_edge = cls(
            buckets=buckets,
            id=id,
            kind=kind,
            relationship=relationship,
            source=source,
            target=target,
            co_episode_count=co_episode_count,
        )

        topology_edge.additional_properties = d
        return topology_edge

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
