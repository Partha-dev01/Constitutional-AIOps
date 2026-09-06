from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.entity_node_metadata import EntityNodeMetadata


T = TypeVar("T", bound="EntityNode")


@_attrs_define
class EntityNode:
    """Entity node - LLM-extracted entity from semantic triplets.

    Attributes:
        id (str):
        name (str):
        metadata (EntityNodeMetadata | Unset):
        relation_count (int | Unset): Number of relations involving this entity Default: 0.
        type_ (str | Unset):  Default: 'entity'.
    """

    id: str
    name: str
    metadata: EntityNodeMetadata | Unset = UNSET
    relation_count: int | Unset = 0
    type_: str | Unset = "entity"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        relation_count = self.relation_count

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if relation_count is not UNSET:
            field_dict["relation_count"] = relation_count
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.entity_node_metadata import EntityNodeMetadata  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        _metadata = d.pop("metadata", UNSET)
        metadata: EntityNodeMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = EntityNodeMetadata.from_dict(_metadata)

        relation_count = d.pop("relation_count", UNSET)

        type_ = d.pop("type", UNSET)

        entity_node = cls(
            id=id,
            name=name,
            metadata=metadata,
            relation_count=relation_count,
            type_=type_,
        )

        entity_node.additional_properties = d
        return entity_node

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
