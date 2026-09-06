from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.root_cause_node_metadata import RootCauseNodeMetadata


T = TypeVar("T", bound="RootCauseNode")


@_attrs_define
class RootCauseNode:
    """Root cause type node - semantic abstraction of failure patterns.

    Attributes:
        id (str):
        name (str):
        avg_resolution_time_minutes (float | Unset): Average time to resolve Default: 0.0.
        frequency (int | Unset): How many episodes caused by this Default: 0.
        metadata (RootCauseNodeMetadata | Unset):
        success_rate (float | Unset): Success rate of resolutions Default: 0.0.
        type_ (str | Unset):  Default: 'root_cause'.
    """

    id: str
    name: str
    avg_resolution_time_minutes: float | Unset = 0.0
    frequency: int | Unset = 0
    metadata: RootCauseNodeMetadata | Unset = UNSET
    success_rate: float | Unset = 0.0
    type_: str | Unset = "root_cause"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        avg_resolution_time_minutes = self.avg_resolution_time_minutes

        frequency = self.frequency

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        success_rate = self.success_rate

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if avg_resolution_time_minutes is not UNSET:
            field_dict["avg_resolution_time_minutes"] = avg_resolution_time_minutes
        if frequency is not UNSET:
            field_dict["frequency"] = frequency
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if success_rate is not UNSET:
            field_dict["success_rate"] = success_rate
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.root_cause_node_metadata import (
            RootCauseNodeMetadata,  # noqa: PLC0415
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        avg_resolution_time_minutes = d.pop("avg_resolution_time_minutes", UNSET)

        frequency = d.pop("frequency", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: RootCauseNodeMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = RootCauseNodeMetadata.from_dict(_metadata)

        success_rate = d.pop("success_rate", UNSET)

        type_ = d.pop("type", UNSET)

        root_cause_node = cls(
            id=id,
            name=name,
            avg_resolution_time_minutes=avg_resolution_time_minutes,
            frequency=frequency,
            metadata=metadata,
            success_rate=success_rate,
            type_=type_,
        )

        root_cause_node.additional_properties = d
        return root_cause_node

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
