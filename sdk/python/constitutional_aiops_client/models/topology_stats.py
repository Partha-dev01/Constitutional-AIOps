from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TopologyStats")


@_attrs_define
class TopologyStats:
    """Aggregate stats for the topology payload.

    Attributes:
        edges (int):
        episodes_in_window (int):
        nodes (int):
        source (str): neo4j | fallback
    """

    edges: int
    episodes_in_window: int
    nodes: int
    source: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        edges = self.edges

        episodes_in_window = self.episodes_in_window

        nodes = self.nodes

        source = self.source

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "edges": edges,
                "episodes_in_window": episodes_in_window,
                "nodes": nodes,
                "source": source,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        edges = d.pop("edges")

        episodes_in_window = d.pop("episodes_in_window")

        nodes = d.pop("nodes")

        source = d.pop("source")

        topology_stats = cls(
            edges=edges,
            episodes_in_window=episodes_in_window,
            nodes=nodes,
            source=source,
        )

        topology_stats.additional_properties = d
        return topology_stats

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
