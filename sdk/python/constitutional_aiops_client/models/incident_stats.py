from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.incident_stats_by_category import IncidentStatsByCategory
    from ..models.incident_stats_by_severity import IncidentStatsBySeverity
    from ..models.incident_stats_by_status import IncidentStatsByStatus


T = TypeVar("T", bound="IncidentStats")


@_attrs_define
class IncidentStats:
    """Incident statistics.

    Attributes:
        by_category (IncidentStatsByCategory):
        by_severity (IncidentStatsBySeverity):
        by_status (IncidentStatsByStatus):
        total (int):
        approval_required_count (int | Unset): Incidents requiring human approval Default: 0.
        auto_resolved_count (int | Unset): Incidents resolved automatically Default: 0.
        mean_time_to_resolution (float | None | Unset): Average resolution time in minutes
    """

    by_category: IncidentStatsByCategory
    by_severity: IncidentStatsBySeverity
    by_status: IncidentStatsByStatus
    total: int
    approval_required_count: int | Unset = 0
    auto_resolved_count: int | Unset = 0
    mean_time_to_resolution: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        by_category = self.by_category.to_dict()

        by_severity = self.by_severity.to_dict()

        by_status = self.by_status.to_dict()

        total = self.total

        approval_required_count = self.approval_required_count

        auto_resolved_count = self.auto_resolved_count

        mean_time_to_resolution: float | None | Unset
        if isinstance(self.mean_time_to_resolution, Unset):
            mean_time_to_resolution = UNSET
        else:
            mean_time_to_resolution = self.mean_time_to_resolution

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "by_category": by_category,
                "by_severity": by_severity,
                "by_status": by_status,
                "total": total,
            }
        )
        if approval_required_count is not UNSET:
            field_dict["approval_required_count"] = approval_required_count
        if auto_resolved_count is not UNSET:
            field_dict["auto_resolved_count"] = auto_resolved_count
        if mean_time_to_resolution is not UNSET:
            field_dict["mean_time_to_resolution"] = mean_time_to_resolution

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.incident_stats_by_category import (
            IncidentStatsByCategory,  # noqa: PLC0415
        )
        from ..models.incident_stats_by_severity import (
            IncidentStatsBySeverity,  # noqa: PLC0415
        )
        from ..models.incident_stats_by_status import (
            IncidentStatsByStatus,  # noqa: PLC0415
        )

        d = dict(src_dict)
        by_category = IncidentStatsByCategory.from_dict(d.pop("by_category"))

        by_severity = IncidentStatsBySeverity.from_dict(d.pop("by_severity"))

        by_status = IncidentStatsByStatus.from_dict(d.pop("by_status"))

        total = d.pop("total")

        approval_required_count = d.pop("approval_required_count", UNSET)

        auto_resolved_count = d.pop("auto_resolved_count", UNSET)

        def _parse_mean_time_to_resolution(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        mean_time_to_resolution = _parse_mean_time_to_resolution(
            d.pop("mean_time_to_resolution", UNSET)
        )

        incident_stats = cls(
            by_category=by_category,
            by_severity=by_severity,
            by_status=by_status,
            total=total,
            approval_required_count=approval_required_count,
            auto_resolved_count=auto_resolved_count,
            mean_time_to_resolution=mean_time_to_resolution,
        )

        incident_stats.additional_properties = d
        return incident_stats

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
