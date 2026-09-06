from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.remediation_step import RemediationStep


T = TypeVar("T", bound="RemediationPlan")


@_attrs_define
class RemediationPlan:
    """Complete remediation plan.

    Attributes:
        created_at (datetime.datetime):
        incident_id (str):
        overall_risk (str):
        plan_id (str):
        requires_approval (bool):
        steps (list[RemediationStep]):
        approved_at (datetime.datetime | None | Unset):
        approved_by (None | str | Unset):
        estimated_duration (None | str | Unset):
    """

    created_at: datetime.datetime
    incident_id: str
    overall_risk: str
    plan_id: str
    requires_approval: bool
    steps: list[RemediationStep]
    approved_at: datetime.datetime | None | Unset = UNSET
    approved_by: None | str | Unset = UNSET
    estimated_duration: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        incident_id = self.incident_id

        overall_risk = self.overall_risk

        plan_id = self.plan_id

        requires_approval = self.requires_approval

        steps = []
        for steps_item_data in self.steps:
            steps_item = steps_item_data.to_dict()
            steps.append(steps_item)

        approved_at: None | str | Unset
        if isinstance(self.approved_at, Unset):
            approved_at = UNSET
        elif isinstance(self.approved_at, datetime.datetime):
            approved_at = self.approved_at.isoformat()
        else:
            approved_at = self.approved_at

        approved_by: None | str | Unset
        if isinstance(self.approved_by, Unset):
            approved_by = UNSET
        else:
            approved_by = self.approved_by

        estimated_duration: None | str | Unset
        if isinstance(self.estimated_duration, Unset):
            estimated_duration = UNSET
        else:
            estimated_duration = self.estimated_duration

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "created_at": created_at,
                "incident_id": incident_id,
                "overall_risk": overall_risk,
                "plan_id": plan_id,
                "requires_approval": requires_approval,
                "steps": steps,
            }
        )
        if approved_at is not UNSET:
            field_dict["approved_at"] = approved_at
        if approved_by is not UNSET:
            field_dict["approved_by"] = approved_by
        if estimated_duration is not UNSET:
            field_dict["estimated_duration"] = estimated_duration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.remediation_step import RemediationStep  # noqa: PLC0415

        d = dict(src_dict)
        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        incident_id = d.pop("incident_id")

        overall_risk = d.pop("overall_risk")

        plan_id = d.pop("plan_id")

        requires_approval = d.pop("requires_approval")

        steps = []
        _steps = d.pop("steps")
        for steps_item_data in _steps:
            steps_item = RemediationStep.from_dict(steps_item_data)

            steps.append(steps_item)

        def _parse_approved_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                approved_at_type_0 = datetime.datetime.fromisoformat(data)

                return approved_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        approved_at = _parse_approved_at(d.pop("approved_at", UNSET))

        def _parse_approved_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        approved_by = _parse_approved_by(d.pop("approved_by", UNSET))

        def _parse_estimated_duration(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        estimated_duration = _parse_estimated_duration(
            d.pop("estimated_duration", UNSET)
        )

        remediation_plan = cls(
            created_at=created_at,
            incident_id=incident_id,
            overall_risk=overall_risk,
            plan_id=plan_id,
            requires_approval=requires_approval,
            steps=steps,
            approved_at=approved_at,
            approved_by=approved_by,
            estimated_duration=estimated_duration,
        )

        remediation_plan.additional_properties = d
        return remediation_plan

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
