from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.topology_edge import TopologyEdge
    from ..models.topology_node import TopologyNode
    from ..models.topology_stats import TopologyStats


T = TypeVar("T", bound="TopologyResponse")


@_attrs_define
class TopologyResponse:
    """Complete platform topology for the schema-mode graph.

    Attributes:
        bucket_minutes (float):
        edges (list[TopologyEdge]):
        generated_at (str):
        nodes (list[TopologyNode]):
        stats (TopologyStats): Aggregate stats for the topology payload.
        window_hours (int):
    """

    bucket_minutes: float
    edges: list[TopologyEdge]
    generated_at: str
    nodes: list[TopologyNode]
    stats: TopologyStats
    window_hours: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bucket_minutes = self.bucket_minutes

        edges = []
        for edges_item_data in self.edges:
            edges_item = edges_item_data.to_dict()
            edges.append(edges_item)

        generated_at = self.generated_at

        nodes = []
        for nodes_item_data in self.nodes:
            nodes_item = nodes_item_data.to_dict()
            nodes.append(nodes_item)

        stats = self.stats.to_dict()

        window_hours = self.window_hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bucket_minutes": bucket_minutes,
                "edges": edges,
                "generated_at": generated_at,
                "nodes": nodes,
                "stats": stats,
                "window_hours": window_hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.topology_edge import TopologyEdge  # noqa: PLC0415
        from ..models.topology_node import TopologyNode  # noqa: PLC0415
        from ..models.topology_stats import TopologyStats  # noqa: PLC0415

        d = dict(src_dict)
        bucket_minutes = d.pop("bucket_minutes")

        edges = []
        _edges = d.pop("edges")
        for edges_item_data in _edges:
            edges_item = TopologyEdge.from_dict(edges_item_data)

            edges.append(edges_item)

        generated_at = d.pop("generated_at")

        nodes = []
        _nodes = d.pop("nodes")
        for nodes_item_data in _nodes:
            nodes_item = TopologyNode.from_dict(nodes_item_data)

            nodes.append(nodes_item)

        stats = TopologyStats.from_dict(d.pop("stats"))

        window_hours = d.pop("window_hours")

        topology_response = cls(
            bucket_minutes=bucket_minutes,
            edges=edges,
            generated_at=generated_at,
            nodes=nodes,
            stats=stats,
            window_hours=window_hours,
        )

        topology_response.additional_properties = d
        return topology_response

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
