from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action_node_metadata import ActionNodeMetadata


T = TypeVar("T", bound="ActionNode")


@_attrs_define
class ActionNode:
    """Action node - remediation actions with success patterns.

    Attributes:
        id (str):
        name (str):
        avg_execution_time_seconds (float | Unset): Average execution time Default: 0.0.
        metadata (ActionNodeMetadata | Unset):
        success_rate (float | Unset): Success rate 0-1 Default: 0.0.
        type_ (str | Unset):  Default: 'action'.
        used_count (int | Unset): Times this action was used Default: 0.
    """

    id: str
    name: str
    avg_execution_time_seconds: float | Unset = 0.0
    metadata: ActionNodeMetadata | Unset = UNSET
    success_rate: float | Unset = 0.0
    type_: str | Unset = "action"
    used_count: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        avg_execution_time_seconds = self.avg_execution_time_seconds

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        success_rate = self.success_rate

        type_ = self.type_

        used_count = self.used_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if avg_execution_time_seconds is not UNSET:
            field_dict["avg_execution_time_seconds"] = avg_execution_time_seconds
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if success_rate is not UNSET:
            field_dict["success_rate"] = success_rate
        if type_ is not UNSET:
            field_dict["type"] = type_
        if used_count is not UNSET:
            field_dict["used_count"] = used_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action_node_metadata import ActionNodeMetadata  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        avg_execution_time_seconds = d.pop("avg_execution_time_seconds", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: ActionNodeMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ActionNodeMetadata.from_dict(_metadata)

        success_rate = d.pop("success_rate", UNSET)

        type_ = d.pop("type", UNSET)

        used_count = d.pop("used_count", UNSET)

        action_node = cls(
            id=id,
            name=name,
            avg_execution_time_seconds=avg_execution_time_seconds,
            metadata=metadata,
            success_rate=success_rate,
            type_=type_,
            used_count=used_count,
        )

        action_node.additional_properties = d
        return action_node

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
