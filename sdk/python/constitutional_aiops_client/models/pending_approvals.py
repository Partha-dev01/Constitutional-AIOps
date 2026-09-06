from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action import Action
    from ..models.pending_approvals_urgency_breakdown import (
        PendingApprovalsUrgencyBreakdown,
    )


T = TypeVar("T", bound="PendingApprovals")


@_attrs_define
class PendingApprovals:
    """Summary of pending approval requests.

    Attributes:
        actions (list[Action]):
        count (int):
        oldest_pending (datetime.datetime | None | Unset):
        urgency_breakdown (PendingApprovalsUrgencyBreakdown | Unset): Count by severity level
    """

    actions: list[Action]
    count: int
    oldest_pending: datetime.datetime | None | Unset = UNSET
    urgency_breakdown: PendingApprovalsUrgencyBreakdown | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        actions = []
        for actions_item_data in self.actions:
            actions_item = actions_item_data.to_dict()
            actions.append(actions_item)

        count = self.count

        oldest_pending: None | str | Unset
        if isinstance(self.oldest_pending, Unset):
            oldest_pending = UNSET
        elif isinstance(self.oldest_pending, datetime.datetime):
            oldest_pending = self.oldest_pending.isoformat()
        else:
            oldest_pending = self.oldest_pending

        urgency_breakdown: dict[str, Any] | Unset = UNSET
        if not isinstance(self.urgency_breakdown, Unset):
            urgency_breakdown = self.urgency_breakdown.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "actions": actions,
                "count": count,
            }
        )
        if oldest_pending is not UNSET:
            field_dict["oldest_pending"] = oldest_pending
        if urgency_breakdown is not UNSET:
            field_dict["urgency_breakdown"] = urgency_breakdown

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action import Action  # noqa: PLC0415
        from ..models.pending_approvals_urgency_breakdown import (
            PendingApprovalsUrgencyBreakdown,  # noqa: PLC0415
        )

        d = dict(src_dict)
        actions = []
        _actions = d.pop("actions")
        for actions_item_data in _actions:
            actions_item = Action.from_dict(actions_item_data)

            actions.append(actions_item)

        count = d.pop("count")

        def _parse_oldest_pending(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                oldest_pending_type_0 = datetime.datetime.fromisoformat(data)

                return oldest_pending_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        oldest_pending = _parse_oldest_pending(d.pop("oldest_pending", UNSET))

        _urgency_breakdown = d.pop("urgency_breakdown", UNSET)
        urgency_breakdown: PendingApprovalsUrgencyBreakdown | Unset
        if isinstance(_urgency_breakdown, Unset):
            urgency_breakdown = UNSET
        else:
            urgency_breakdown = PendingApprovalsUrgencyBreakdown.from_dict(
                _urgency_breakdown
            )

        pending_approvals = cls(
            actions=actions,
            count=count,
            oldest_pending=oldest_pending,
            urgency_breakdown=urgency_breakdown,
        )

        pending_approvals.additional_properties = d
        return pending_approvals

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
