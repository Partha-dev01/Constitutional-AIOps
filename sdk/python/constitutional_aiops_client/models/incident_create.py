from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.incident_category import IncidentCategory
from ..models.incident_severity import IncidentSeverity
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.service_info import ServiceInfo
    from ..models.telemetry_snapshot import TelemetrySnapshot


T = TypeVar("T", bound="IncidentCreate")


@_attrs_define
class IncidentCreate:
    """Request to create a new incident.

    Example:
        {'affected_services': [{'name': 'payment-service', 'namespace': 'production'}], 'auto_analyze': True,
            'category': 'performance', 'description': 'Users reporting slow checkout times', 'severity': 'high', 'source':
            'alert', 'tags': ['checkout', 'latency'], 'title': 'High latency on payment-service'}

    Attributes:
        affected_services (list[ServiceInfo]): List of affected services
        severity (IncidentSeverity): Incident severity levels.
        title (str): Incident title
        auto_analyze (bool | Unset): Automatically trigger RCA Default: True.
        category (IncidentCategory | Unset): Incident category types.
        description (None | str | Unset): Detailed description
        source (str | Unset): Source of incident (manual, alert, telemetry) Default: 'manual'.
        tags (list[str] | None | Unset): Custom tags
        telemetry (None | TelemetrySnapshot | Unset): Initial telemetry data
    """

    affected_services: list[ServiceInfo]
    severity: IncidentSeverity
    title: str
    auto_analyze: bool | Unset = True
    category: IncidentCategory | Unset = UNSET
    description: None | str | Unset = UNSET
    source: str | Unset = "manual"
    tags: list[str] | None | Unset = UNSET
    telemetry: None | TelemetrySnapshot | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.telemetry_snapshot import TelemetrySnapshot  # noqa: PLC0415

        affected_services = []
        for affected_services_item_data in self.affected_services:
            affected_services_item = affected_services_item_data.to_dict()
            affected_services.append(affected_services_item)

        severity = self.severity.value

        title = self.title

        auto_analyze = self.auto_analyze

        category: str | Unset = UNSET
        if not isinstance(self.category, Unset):
            category = self.category.value

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        source = self.source

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        telemetry: dict[str, Any] | None | Unset
        if isinstance(self.telemetry, Unset):
            telemetry = UNSET
        elif isinstance(self.telemetry, TelemetrySnapshot):
            telemetry = self.telemetry.to_dict()
        else:
            telemetry = self.telemetry

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "affected_services": affected_services,
                "severity": severity,
                "title": title,
            }
        )
        if auto_analyze is not UNSET:
            field_dict["auto_analyze"] = auto_analyze
        if category is not UNSET:
            field_dict["category"] = category
        if description is not UNSET:
            field_dict["description"] = description
        if source is not UNSET:
            field_dict["source"] = source
        if tags is not UNSET:
            field_dict["tags"] = tags
        if telemetry is not UNSET:
            field_dict["telemetry"] = telemetry

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_info import ServiceInfo  # noqa: PLC0415
        from ..models.telemetry_snapshot import TelemetrySnapshot  # noqa: PLC0415

        d = dict(src_dict)
        affected_services = []
        _affected_services = d.pop("affected_services")
        for affected_services_item_data in _affected_services:
            affected_services_item = ServiceInfo.from_dict(affected_services_item_data)

            affected_services.append(affected_services_item)

        severity = IncidentSeverity(d.pop("severity"))

        title = d.pop("title")

        auto_analyze = d.pop("auto_analyze", UNSET)

        _category = d.pop("category", UNSET)
        category: IncidentCategory | Unset
        if isinstance(_category, Unset):
            category = UNSET
        else:
            category = IncidentCategory(_category)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        source = d.pop("source", UNSET)

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

        def _parse_telemetry(data: object) -> None | TelemetrySnapshot | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                telemetry_type_0 = TelemetrySnapshot.from_dict(data)

                return telemetry_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TelemetrySnapshot | Unset, data)

        telemetry = _parse_telemetry(d.pop("telemetry", UNSET))

        incident_create = cls(
            affected_services=affected_services,
            severity=severity,
            title=title,
            auto_analyze=auto_analyze,
            category=category,
            description=description,
            source=source,
            tags=tags,
            telemetry=telemetry,
        )

        incident_create.additional_properties = d
        return incident_create

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
