from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.generate_schema_response_edges_item import (
        GenerateSchemaResponseEdgesItem,
    )
    from ..models.generate_schema_response_nodes_item import (
        GenerateSchemaResponseNodesItem,
    )


T = TypeVar("T", bound="GenerateSchemaResponse")


@_attrs_define
class GenerateSchemaResponse:
    """A validated candidate schema returned as a PREVIEW (not persisted).

    Attributes:
        edges (list[GenerateSchemaResponseEdgesItem]):
        nodes (list[GenerateSchemaResponseNodesItem]):
        note (str | Unset): Optional info note (e.g. retry happened) Default: ''.
        preview (bool | Unset):  Default: True.
    """

    edges: list[GenerateSchemaResponseEdgesItem]
    nodes: list[GenerateSchemaResponseNodesItem]
    note: str | Unset = ""
    preview: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        edges = []
        for edges_item_data in self.edges:
            edges_item = edges_item_data.to_dict()
            edges.append(edges_item)

        nodes = []
        for nodes_item_data in self.nodes:
            nodes_item = nodes_item_data.to_dict()
            nodes.append(nodes_item)

        note = self.note

        preview = self.preview

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "edges": edges,
                "nodes": nodes,
            }
        )
        if note is not UNSET:
            field_dict["note"] = note
        if preview is not UNSET:
            field_dict["preview"] = preview

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.generate_schema_response_edges_item import (
            GenerateSchemaResponseEdgesItem,  # noqa: PLC0415
        )
        from ..models.generate_schema_response_nodes_item import (
            GenerateSchemaResponseNodesItem,  # noqa: PLC0415
        )

        d = dict(src_dict)
        edges = []
        _edges = d.pop("edges")
        for edges_item_data in _edges:
            edges_item = GenerateSchemaResponseEdgesItem.from_dict(edges_item_data)

            edges.append(edges_item)

        nodes = []
        _nodes = d.pop("nodes")
        for nodes_item_data in _nodes:
            nodes_item = GenerateSchemaResponseNodesItem.from_dict(nodes_item_data)

            nodes.append(nodes_item)

        note = d.pop("note", UNSET)

        preview = d.pop("preview", UNSET)

        generate_schema_response = cls(
            edges=edges,
            nodes=nodes,
            note=note,
            preview=preview,
        )

        generate_schema_response.additional_properties = d
        return generate_schema_response

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
