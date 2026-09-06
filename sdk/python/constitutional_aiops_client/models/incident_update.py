from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.incident_category import IncidentCategory
from ..models.incident_severity import IncidentSeverity
from ..models.incident_status import IncidentStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="IncidentUpdate")


@_attrs_define
class IncidentUpdate:
    """Request to update an incident.

    Example:
        {'resolution_notes': 'Increased connection pool size from 10 to 50', 'status': 'resolved'}

    Attributes:
        category (IncidentCategory | None | Unset):
        description (None | str | Unset):
        resolution_notes (None | str | Unset):
        severity (IncidentSeverity | None | Unset):
        status (IncidentStatus | None | Unset):
        tags (list[str] | None | Unset):
        title (None | str | Unset):
    """

    category: IncidentCategory | None | Unset = UNSET
    description: None | str | Unset = UNSET
    resolution_notes: None | str | Unset = UNSET
    severity: IncidentSeverity | None | Unset = UNSET
    status: IncidentStatus | None | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    title: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        category: None | str | Unset
        if isinstance(self.category, Unset):
            category = UNSET
        elif isinstance(self.category, IncidentCategory):
            category = self.category.value
        else:
            category = self.category

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        resolution_notes: None | str | Unset
        if isinstance(self.resolution_notes, Unset):
            resolution_notes = UNSET
        else:
            resolution_notes = self.resolution_notes

        severity: None | str | Unset
        if isinstance(self.severity, Unset):
            severity = UNSET
        elif isinstance(self.severity, IncidentSeverity):
            severity = self.severity.value
        else:
            severity = self.severity

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, IncidentStatus):
            status = self.status.value
        else:
            status = self.status

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        title: None | str | Unset
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if category is not UNSET:
            field_dict["category"] = category
        if description is not UNSET:
            field_dict["description"] = description
        if resolution_notes is not UNSET:
            field_dict["resolution_notes"] = resolution_notes
        if severity is not UNSET:
            field_dict["severity"] = severity
        if status is not UNSET:
            field_dict["status"] = status
        if tags is not UNSET:
            field_dict["tags"] = tags
        if title is not UNSET:
            field_dict["title"] = title

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_category(data: object) -> IncidentCategory | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                category_type_0 = IncidentCategory(data)

                return category_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(IncidentCategory | None | Unset, data)

        category = _parse_category(d.pop("category", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_resolution_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        resolution_notes = _parse_resolution_notes(d.pop("resolution_notes", UNSET))

        def _parse_severity(data: object) -> IncidentSeverity | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                severity_type_0 = IncidentSeverity(data)

                return severity_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(IncidentSeverity | None | Unset, data)

        severity = _parse_severity(d.pop("severity", UNSET))

        def _parse_status(data: object) -> IncidentStatus | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = IncidentStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(IncidentStatus | None | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_tags(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        def _parse_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        title = _parse_title(d.pop("title", UNSET))

        incident_update = cls(
            category=category,
            description=description,
            resolution_notes=resolution_notes,
            severity=severity,
            status=status,
            tags=tags,
            title=title,
        )

        incident_update.additional_properties = d
        return incident_update

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
