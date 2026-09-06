from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.episode_metadata import EpisodeMetadata


T = TypeVar("T", bound="Episode")


@_attrs_define
class Episode:
    """Episode from episodic memory (legacy).

    Attributes:
        category (str):
        id (str):
        services (list[str]):
        severity (str):
        timestamp (datetime.datetime):
        title (str):
        confidence (float | Unset):  Default: 0.0.
        metadata (EpisodeMetadata | Unset):
        resolution (None | str | Unset):
        root_cause (None | str | Unset):
    """

    category: str
    id: str
    services: list[str]
    severity: str
    timestamp: datetime.datetime
    title: str
    confidence: float | Unset = 0.0
    metadata: EpisodeMetadata | Unset = UNSET
    resolution: None | str | Unset = UNSET
    root_cause: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        category = self.category

        id = self.id

        services = self.services

        severity = self.severity

        timestamp = self.timestamp.isoformat()

        title = self.title

        confidence = self.confidence

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        resolution: None | str | Unset
        if isinstance(self.resolution, Unset):
            resolution = UNSET
        else:
            resolution = self.resolution

        root_cause: None | str | Unset
        if isinstance(self.root_cause, Unset):
            root_cause = UNSET
        else:
            root_cause = self.root_cause

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "category": category,
                "id": id,
                "services": services,
                "severity": severity,
                "timestamp": timestamp,
                "title": title,
            }
        )
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if resolution is not UNSET:
            field_dict["resolution"] = resolution
        if root_cause is not UNSET:
            field_dict["root_cause"] = root_cause

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.episode_metadata import EpisodeMetadata  # noqa: PLC0415

        d = dict(src_dict)
        category = d.pop("category")

        id = d.pop("id")

        services = cast(list[str], d.pop("services"))

        severity = d.pop("severity")

        timestamp = datetime.datetime.fromisoformat(d.pop("timestamp"))

        title = d.pop("title")

        confidence = d.pop("confidence", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: EpisodeMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = EpisodeMetadata.from_dict(_metadata)

        def _parse_resolution(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        resolution = _parse_resolution(d.pop("resolution", UNSET))

        def _parse_root_cause(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        root_cause = _parse_root_cause(d.pop("root_cause", UNSET))

        episode = cls(
            category=category,
            id=id,
            services=services,
            severity=severity,
            timestamp=timestamp,
            title=title,
            confidence=confidence,
            metadata=metadata,
            resolution=resolution,
            root_cause=root_cause,
        )

        episode.additional_properties = d
        return episode

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
