from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.episode_node_metadata import EpisodeNodeMetadata


T = TypeVar("T", bound="EpisodeNode")


@_attrs_define
class EpisodeNode:
    """Episode node - a complete incident lifecycle.

    Attributes:
        category (str):
        id (str):
        severity (str):
        timestamp (datetime.datetime):
        title (str):
        confidence (float | Unset):  Default: 0.0.
        metadata (EpisodeNodeMetadata | Unset):
        resolution_time_minutes (float | None | Unset):
        root_cause (None | str | Unset):
        services (list[str] | Unset):
        status (str | Unset):  Default: 'resolved'.
        successful_actions (list[str] | Unset):
        type_ (str | Unset):  Default: 'episode'.
    """

    category: str
    id: str
    severity: str
    timestamp: datetime.datetime
    title: str
    confidence: float | Unset = 0.0
    metadata: EpisodeNodeMetadata | Unset = UNSET
    resolution_time_minutes: float | None | Unset = UNSET
    root_cause: None | str | Unset = UNSET
    services: list[str] | Unset = UNSET
    status: str | Unset = "resolved"
    successful_actions: list[str] | Unset = UNSET
    type_: str | Unset = "episode"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        category = self.category

        id = self.id

        severity = self.severity

        timestamp = self.timestamp.isoformat()

        title = self.title

        confidence = self.confidence

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        resolution_time_minutes: float | None | Unset
        if isinstance(self.resolution_time_minutes, Unset):
            resolution_time_minutes = UNSET
        else:
            resolution_time_minutes = self.resolution_time_minutes

        root_cause: None | str | Unset
        if isinstance(self.root_cause, Unset):
            root_cause = UNSET
        else:
            root_cause = self.root_cause

        services: list[str] | Unset = UNSET
        if not isinstance(self.services, Unset):
            services = self.services

        status = self.status

        successful_actions: list[str] | Unset = UNSET
        if not isinstance(self.successful_actions, Unset):
            successful_actions = self.successful_actions

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "category": category,
                "id": id,
                "severity": severity,
                "timestamp": timestamp,
                "title": title,
            }
        )
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if resolution_time_minutes is not UNSET:
            field_dict["resolution_time_minutes"] = resolution_time_minutes
        if root_cause is not UNSET:
            field_dict["root_cause"] = root_cause
        if services is not UNSET:
            field_dict["services"] = services
        if status is not UNSET:
            field_dict["status"] = status
        if successful_actions is not UNSET:
            field_dict["successful_actions"] = successful_actions
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.episode_node_metadata import EpisodeNodeMetadata  # noqa: PLC0415

        d = dict(src_dict)
        category = d.pop("category")

        id = d.pop("id")

        severity = d.pop("severity")

        timestamp = datetime.datetime.fromisoformat(d.pop("timestamp"))

        title = d.pop("title")

        confidence = d.pop("confidence", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: EpisodeNodeMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = EpisodeNodeMetadata.from_dict(_metadata)

        def _parse_resolution_time_minutes(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        resolution_time_minutes = _parse_resolution_time_minutes(
            d.pop("resolution_time_minutes", UNSET)
        )

        def _parse_root_cause(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        root_cause = _parse_root_cause(d.pop("root_cause", UNSET))

        services = cast(list[str], d.pop("services", UNSET))

        status = d.pop("status", UNSET)

        successful_actions = cast(list[str], d.pop("successful_actions", UNSET))

        type_ = d.pop("type", UNSET)

        episode_node = cls(
            category=category,
            id=id,
            severity=severity,
            timestamp=timestamp,
            title=title,
            confidence=confidence,
            metadata=metadata,
            resolution_time_minutes=resolution_time_minutes,
            root_cause=root_cause,
            services=services,
            status=status,
            successful_actions=successful_actions,
            type_=type_,
        )

        episode_node.additional_properties = d
        return episode_node

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
