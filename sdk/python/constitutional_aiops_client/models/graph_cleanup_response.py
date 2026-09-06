from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GraphCleanupResponse")


@_attrs_define
class GraphCleanupResponse:
    """Response from graph cleanup operation.

    Attributes:
        success (bool):
        entities_merged (int | Unset):  Default: 0.
        message (str | Unset):  Default: ''.
        old_episodes_deleted (int | Unset):  Default: 0.
        orphan_entities_deleted (int | Unset):  Default: 0.
        similar_to_deleted (int | Unset):  Default: 0.
    """

    success: bool
    entities_merged: int | Unset = 0
    message: str | Unset = ""
    old_episodes_deleted: int | Unset = 0
    orphan_entities_deleted: int | Unset = 0
    similar_to_deleted: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        entities_merged = self.entities_merged

        message = self.message

        old_episodes_deleted = self.old_episodes_deleted

        orphan_entities_deleted = self.orphan_entities_deleted

        similar_to_deleted = self.similar_to_deleted

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
            }
        )
        if entities_merged is not UNSET:
            field_dict["entities_merged"] = entities_merged
        if message is not UNSET:
            field_dict["message"] = message
        if old_episodes_deleted is not UNSET:
            field_dict["old_episodes_deleted"] = old_episodes_deleted
        if orphan_entities_deleted is not UNSET:
            field_dict["orphan_entities_deleted"] = orphan_entities_deleted
        if similar_to_deleted is not UNSET:
            field_dict["similar_to_deleted"] = similar_to_deleted

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        success = d.pop("success")

        entities_merged = d.pop("entities_merged", UNSET)

        message = d.pop("message", UNSET)

        old_episodes_deleted = d.pop("old_episodes_deleted", UNSET)

        orphan_entities_deleted = d.pop("orphan_entities_deleted", UNSET)

        similar_to_deleted = d.pop("similar_to_deleted", UNSET)

        graph_cleanup_response = cls(
            success=success,
            entities_merged=entities_merged,
            message=message,
            old_episodes_deleted=old_episodes_deleted,
            orphan_entities_deleted=orphan_entities_deleted,
            similar_to_deleted=similar_to_deleted,
        )

        graph_cleanup_response.additional_properties = d
        return graph_cleanup_response

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
