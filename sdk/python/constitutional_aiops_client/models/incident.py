from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.incident_category import IncidentCategory
from ..models.incident_severity import IncidentSeverity
from ..models.incident_status import IncidentStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.rca_result import RCAResult
    from ..models.remediation_plan import RemediationPlan
    from ..models.service_info import ServiceInfo
    from ..models.telemetry_snapshot import TelemetrySnapshot


T = TypeVar("T", bound="Incident")


@_attrs_define
class Incident:
    """Complete incident record.

    Example:
        {'affected_services': [{'name': 'payment-service', 'namespace': 'production'}], 'category': 'performance',
            'created_at': '2025-12-14T10:00:00Z', 'description': 'Users reporting slow checkout times', 'id':
            'INC-2024-042', 'severity': 'high', 'source': 'alert', 'status': 'analyzing', 'tags': ['checkout', 'latency'],
            'title': 'High latency on payment-service', 'updated_at': '2025-12-14T10:15:00Z'}

    Attributes:
        affected_services (list[ServiceInfo]): List of affected services
        created_at (datetime.datetime):
        id (str): Unique incident ID (e.g., INC-2024-042)
        severity (IncidentSeverity): Incident severity levels.
        source (str):
        title (str): Incident title
        updated_at (datetime.datetime):
        assigned_to (None | str | Unset):
        category (IncidentCategory | Unset): Incident category types.
        description (None | str | Unset): Detailed description
        detected_at (datetime.datetime | None | Unset):
        rca (None | RCAResult | Unset):
        remediation_plan (None | RemediationPlan | Unset):
        resolution_notes (None | str | Unset):
        resolved_at (datetime.datetime | None | Unset):
        similar_incidents (list[str] | None | Unset): Related incident IDs from graph memory
        status (IncidentStatus | Unset): Incident lifecycle status.
        tags (list[str] | None | Unset): Custom tags
        telemetry (None | TelemetrySnapshot | Unset):
    """

    affected_services: list[ServiceInfo]
    created_at: datetime.datetime
    id: str
    severity: IncidentSeverity
    source: str
    title: str
    updated_at: datetime.datetime
    assigned_to: None | str | Unset = UNSET
    category: IncidentCategory | Unset = UNSET
    description: None | str | Unset = UNSET
    detected_at: datetime.datetime | None | Unset = UNSET
    rca: None | RCAResult | Unset = UNSET
    remediation_plan: None | RemediationPlan | Unset = UNSET
    resolution_notes: None | str | Unset = UNSET
    resolved_at: datetime.datetime | None | Unset = UNSET
    similar_incidents: list[str] | None | Unset = UNSET
    status: IncidentStatus | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    telemetry: None | TelemetrySnapshot | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.rca_result import RCAResult  # noqa: PLC0415
        from ..models.remediation_plan import RemediationPlan  # noqa: PLC0415
        from ..models.telemetry_snapshot import TelemetrySnapshot  # noqa: PLC0415

        affected_services = []
        for affected_services_item_data in self.affected_services:
            affected_services_item = affected_services_item_data.to_dict()
            affected_services.append(affected_services_item)

        created_at = self.created_at.isoformat()

        id = self.id

        severity = self.severity.value

        source = self.source

        title = self.title

        updated_at = self.updated_at.isoformat()

        assigned_to: None | str | Unset
        if isinstance(self.assigned_to, Unset):
            assigned_to = UNSET
        else:
            assigned_to = self.assigned_to

        category: str | Unset = UNSET
        if not isinstance(self.category, Unset):
            category = self.category.value

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        detected_at: None | str | Unset
        if isinstance(self.detected_at, Unset):
            detected_at = UNSET
        elif isinstance(self.detected_at, datetime.datetime):
            detected_at = self.detected_at.isoformat()
        else:
            detected_at = self.detected_at

        rca: dict[str, Any] | None | Unset
        if isinstance(self.rca, Unset):
            rca = UNSET
        elif isinstance(self.rca, RCAResult):
            rca = self.rca.to_dict()
        else:
            rca = self.rca

        remediation_plan: dict[str, Any] | None | Unset
        if isinstance(self.remediation_plan, Unset):
            remediation_plan = UNSET
        elif isinstance(self.remediation_plan, RemediationPlan):
            remediation_plan = self.remediation_plan.to_dict()
        else:
            remediation_plan = self.remediation_plan

        resolution_notes: None | str | Unset
        if isinstance(self.resolution_notes, Unset):
            resolution_notes = UNSET
        else:
            resolution_notes = self.resolution_notes

        resolved_at: None | str | Unset
        if isinstance(self.resolved_at, Unset):
            resolved_at = UNSET
        elif isinstance(self.resolved_at, datetime.datetime):
            resolved_at = self.resolved_at.isoformat()
        else:
            resolved_at = self.resolved_at

        similar_incidents: list[str] | None | Unset
        if isinstance(self.similar_incidents, Unset):
            similar_incidents = UNSET
        elif isinstance(self.similar_incidents, list):
            similar_incidents = self.similar_incidents

        else:
            similar_incidents = self.similar_incidents

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

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
                "created_at": created_at,
                "id": id,
                "severity": severity,
                "source": source,
                "title": title,
                "updated_at": updated_at,
            }
        )
        if assigned_to is not UNSET:
            field_dict["assigned_to"] = assigned_to
        if category is not UNSET:
            field_dict["category"] = category
        if description is not UNSET:
            field_dict["description"] = description
        if detected_at is not UNSET:
            field_dict["detected_at"] = detected_at
        if rca is not UNSET:
            field_dict["rca"] = rca
        if remediation_plan is not UNSET:
            field_dict["remediation_plan"] = remediation_plan
        if resolution_notes is not UNSET:
            field_dict["resolution_notes"] = resolution_notes
        if resolved_at is not UNSET:
            field_dict["resolved_at"] = resolved_at
        if similar_incidents is not UNSET:
            field_dict["similar_incidents"] = similar_incidents
        if status is not UNSET:
            field_dict["status"] = status
        if tags is not UNSET:
            field_dict["tags"] = tags
        if telemetry is not UNSET:
            field_dict["telemetry"] = telemetry

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.rca_result import RCAResult  # noqa: PLC0415
        from ..models.remediation_plan import RemediationPlan  # noqa: PLC0415
        from ..models.service_info import ServiceInfo  # noqa: PLC0415
        from ..models.telemetry_snapshot import TelemetrySnapshot  # noqa: PLC0415

        d = dict(src_dict)
        affected_services = []
        _affected_services = d.pop("affected_services")
        for affected_services_item_data in _affected_services:
            affected_services_item = ServiceInfo.from_dict(affected_services_item_data)

            affected_services.append(affected_services_item)

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        id = d.pop("id")

        severity = IncidentSeverity(d.pop("severity"))

        source = d.pop("source")

        title = d.pop("title")

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_assigned_to(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assigned_to = _parse_assigned_to(d.pop("assigned_to", UNSET))

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

        def _parse_detected_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                detected_at_type_0 = datetime.datetime.fromisoformat(data)

                return detected_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        detected_at = _parse_detected_at(d.pop("detected_at", UNSET))

        def _parse_rca(data: object) -> None | RCAResult | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                rca_type_0 = RCAResult.from_dict(data)

                return rca_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RCAResult | Unset, data)

        rca = _parse_rca(d.pop("rca", UNSET))

        def _parse_remediation_plan(data: object) -> None | RemediationPlan | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                remediation_plan_type_0 = RemediationPlan.from_dict(data)

                return remediation_plan_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RemediationPlan | Unset, data)

        remediation_plan = _parse_remediation_plan(d.pop("remediation_plan", UNSET))

        def _parse_resolution_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        resolution_notes = _parse_resolution_notes(d.pop("resolution_notes", UNSET))

        def _parse_resolved_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                resolved_at_type_0 = datetime.datetime.fromisoformat(data)

                return resolved_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        resolved_at = _parse_resolved_at(d.pop("resolved_at", UNSET))

        def _parse_similar_incidents(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                similar_incidents_type_0 = cast(list[str], data)

                return similar_incidents_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        similar_incidents = _parse_similar_incidents(d.pop("similar_incidents", UNSET))

        _status = d.pop("status", UNSET)
        status: IncidentStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = IncidentStatus(_status)

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

        incident = cls(
            affected_services=affected_services,
            created_at=created_at,
            id=id,
            severity=severity,
            source=source,
            title=title,
            updated_at=updated_at,
            assigned_to=assigned_to,
            category=category,
            description=description,
            detected_at=detected_at,
            rca=rca,
            remediation_plan=remediation_plan,
            resolution_notes=resolution_notes,
            resolved_at=resolved_at,
            similar_incidents=similar_incidents,
            status=status,
            tags=tags,
            telemetry=telemetry,
        )

        incident.additional_properties = d
        return incident

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
