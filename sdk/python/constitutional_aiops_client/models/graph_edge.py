from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.graph_edge_metadata import GraphEdgeMetadata


T = TypeVar("T", bound="GraphEdge")


@_attrs_define
class GraphEdge:
    """Graph edge with relationship type.

    Attributes:
        relationship (str):
        source (str):
        target (str):
        metadata (GraphEdgeMetadata | Unset):
        weight (float | Unset): Edge weight (e.g., similarity score) Default: 1.0.
    """

    relationship: str
    source: str
    target: str
    metadata: GraphEdgeMetadata | Unset = UNSET
    weight: float | Unset = 1.0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        relationship = self.relationship

        source = self.source

        target = self.target

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        weight = self.weight

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "relationship": relationship,
                "source": source,
                "target": target,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if weight is not UNSET:
            field_dict["weight"] = weight

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.graph_edge_metadata import GraphEdgeMetadata  # noqa: PLC0415

        d = dict(src_dict)
        relationship = d.pop("relationship")

        source = d.pop("source")

        target = d.pop("target")

        _metadata = d.pop("metadata", UNSET)
        metadata: GraphEdgeMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = GraphEdgeMetadata.from_dict(_metadata)

        weight = d.pop("weight", UNSET)

        graph_edge = cls(
            relationship=relationship,
            source=source,
            target=target,
            metadata=metadata,
            weight=weight,
        )

        graph_edge.additional_properties = d
        return graph_edge

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
