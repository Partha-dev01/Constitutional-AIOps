from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GraphCleanupRequest")


@_attrs_define
class GraphCleanupRequest:
    """Request for graph cleanup operation.

    Attributes:
        delete_orphan_entities (bool | Unset): Delete orphan entities Default: True.
        delete_similar_to (bool | Unset): Delete all SIMILAR_TO edges Default: True.
        keep_episodes (int | Unset): Keep N most recent episodes (0=all) Default: 50.
        merge_duplicate_entities (bool | Unset): Merge duplicate entities Default: True.
    """

    delete_orphan_entities: bool | Unset = True
    delete_similar_to: bool | Unset = True
    keep_episodes: int | Unset = 50
    merge_duplicate_entities: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        delete_orphan_entities = self.delete_orphan_entities

        delete_similar_to = self.delete_similar_to

        keep_episodes = self.keep_episodes

        merge_duplicate_entities = self.merge_duplicate_entities

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if delete_orphan_entities is not UNSET:
            field_dict["delete_orphan_entities"] = delete_orphan_entities
        if delete_similar_to is not UNSET:
            field_dict["delete_similar_to"] = delete_similar_to
        if keep_episodes is not UNSET:
            field_dict["keep_episodes"] = keep_episodes
        if merge_duplicate_entities is not UNSET:
            field_dict["merge_duplicate_entities"] = merge_duplicate_entities

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        delete_orphan_entities = d.pop("delete_orphan_entities", UNSET)

        delete_similar_to = d.pop("delete_similar_to", UNSET)

        keep_episodes = d.pop("keep_episodes", UNSET)

        merge_duplicate_entities = d.pop("merge_duplicate_entities", UNSET)

        graph_cleanup_request = cls(
            delete_orphan_entities=delete_orphan_entities,
            delete_similar_to=delete_similar_to,
            keep_episodes=keep_episodes,
            merge_duplicate_entities=merge_duplicate_entities,
        )

        graph_cleanup_request.additional_properties = d
        return graph_cleanup_request

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
