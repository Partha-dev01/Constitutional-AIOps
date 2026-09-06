from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action_stats_by_status import ActionStatsByStatus
    from ..models.action_stats_by_type import ActionStatsByType


T = TypeVar("T", bound="ActionStats")


@_attrs_define
class ActionStats:
    """Action execution statistics.

    Attributes:
        auto_executed (int): Actions executed automatically
        by_status (ActionStatsByStatus):
        by_type (ActionStatsByType):
        human_approved (int): Actions requiring human approval
        rejected (int): Actions rejected by Constitutional AI
        success_rate (float): Successful execution rate
        total (int):
        avg_execution_time_ms (float | None | Unset):
    """

    auto_executed: int
    by_status: ActionStatsByStatus
    by_type: ActionStatsByType
    human_approved: int
    rejected: int
    success_rate: float
    total: int
    avg_execution_time_ms: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_executed = self.auto_executed

        by_status = self.by_status.to_dict()

        by_type = self.by_type.to_dict()

        human_approved = self.human_approved

        rejected = self.rejected

        success_rate = self.success_rate

        total = self.total

        avg_execution_time_ms: float | None | Unset
        if isinstance(self.avg_execution_time_ms, Unset):
            avg_execution_time_ms = UNSET
        else:
            avg_execution_time_ms = self.avg_execution_time_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "auto_executed": auto_executed,
                "by_status": by_status,
                "by_type": by_type,
                "human_approved": human_approved,
                "rejected": rejected,
                "success_rate": success_rate,
                "total": total,
            }
        )
        if avg_execution_time_ms is not UNSET:
            field_dict["avg_execution_time_ms"] = avg_execution_time_ms

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action_stats_by_status import ActionStatsByStatus  # noqa: PLC0415
        from ..models.action_stats_by_type import ActionStatsByType  # noqa: PLC0415

        d = dict(src_dict)
        auto_executed = d.pop("auto_executed")

        by_status = ActionStatsByStatus.from_dict(d.pop("by_status"))

        by_type = ActionStatsByType.from_dict(d.pop("by_type"))

        human_approved = d.pop("human_approved")

        rejected = d.pop("rejected")

        success_rate = d.pop("success_rate")

        total = d.pop("total")

        def _parse_avg_execution_time_ms(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_execution_time_ms = _parse_avg_execution_time_ms(
            d.pop("avg_execution_time_ms", UNSET)
        )

        action_stats = cls(
            auto_executed=auto_executed,
            by_status=by_status,
            by_type=by_type,
            human_approved=human_approved,
            rejected=rejected,
            success_rate=success_rate,
            total=total,
            avg_execution_time_ms=avg_execution_time_ms,
        )

        action_stats.additional_properties = d
        return action_stats

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
