from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.topology_schema_update_edges_item import TopologySchemaUpdateEdgesItem
    from ..models.topology_schema_update_nodes_item import TopologySchemaUpdateNodesItem


T = TypeVar("T", bound="TopologySchemaUpdate")


@_attrs_define
class TopologySchemaUpdate:
    """An operator-edited schema to validate + persist (the 'Apply' request).

    Attributes:
        edges (list[TopologySchemaUpdateEdgesItem] | Unset):
        nodes (list[TopologySchemaUpdateNodesItem] | Unset):
    """

    edges: list[TopologySchemaUpdateEdgesItem] | Unset = UNSET
    nodes: list[TopologySchemaUpdateNodesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        edges: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.edges, Unset):
            edges = []
            for edges_item_data in self.edges:
                edges_item = edges_item_data.to_dict()
                edges.append(edges_item)

        nodes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.nodes, Unset):
            nodes = []
            for nodes_item_data in self.nodes:
                nodes_item = nodes_item_data.to_dict()
                nodes.append(nodes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if edges is not UNSET:
            field_dict["edges"] = edges
        if nodes is not UNSET:
            field_dict["nodes"] = nodes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.topology_schema_update_edges_item import (
            TopologySchemaUpdateEdgesItem,  # noqa: PLC0415
        )
        from ..models.topology_schema_update_nodes_item import (
            TopologySchemaUpdateNodesItem,  # noqa: PLC0415
        )

        d = dict(src_dict)
        _edges = d.pop("edges", UNSET)
        edges: list[TopologySchemaUpdateEdgesItem] | Unset = UNSET
        if _edges is not UNSET:
            edges = []
            for edges_item_data in _edges:
                edges_item = TopologySchemaUpdateEdgesItem.from_dict(edges_item_data)

                edges.append(edges_item)

        _nodes = d.pop("nodes", UNSET)
        nodes: list[TopologySchemaUpdateNodesItem] | Unset = UNSET
        if _nodes is not UNSET:
            nodes = []
            for nodes_item_data in _nodes:
                nodes_item = TopologySchemaUpdateNodesItem.from_dict(nodes_item_data)

                nodes.append(nodes_item)

        topology_schema_update = cls(
            edges=edges,
            nodes=nodes,
        )

        topology_schema_update.additional_properties = d
        return topology_schema_update

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
