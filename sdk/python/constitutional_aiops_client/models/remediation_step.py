from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RemediationStep")


@_attrs_define
class RemediationStep:
    """Single remediation step.

    Attributes:
        action (str):
        order (int):
        risk (str):
        command (None | str | Unset):
        executed_at (datetime.datetime | None | Unset):
        requires_approval (bool | Unset):  Default: False.
        result (None | str | Unset):
        status (str | Unset):  Default: 'pending'.
    """

    action: str
    order: int
    risk: str
    command: None | str | Unset = UNSET
    executed_at: datetime.datetime | None | Unset = UNSET
    requires_approval: bool | Unset = False
    result: None | str | Unset = UNSET
    status: str | Unset = "pending"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        action = self.action

        order = self.order

        risk = self.risk

        command: None | str | Unset
        if isinstance(self.command, Unset):
            command = UNSET
        else:
            command = self.command

        executed_at: None | str | Unset
        if isinstance(self.executed_at, Unset):
            executed_at = UNSET
        elif isinstance(self.executed_at, datetime.datetime):
            executed_at = self.executed_at.isoformat()
        else:
            executed_at = self.executed_at

        requires_approval = self.requires_approval

        result: None | str | Unset
        if isinstance(self.result, Unset):
            result = UNSET
        else:
            result = self.result

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action": action,
                "order": order,
                "risk": risk,
            }
        )
        if command is not UNSET:
            field_dict["command"] = command
        if executed_at is not UNSET:
            field_dict["executed_at"] = executed_at
        if requires_approval is not UNSET:
            field_dict["requires_approval"] = requires_approval
        if result is not UNSET:
            field_dict["result"] = result
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = d.pop("action")

        order = d.pop("order")

        risk = d.pop("risk")

        def _parse_command(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        command = _parse_command(d.pop("command", UNSET))

        def _parse_executed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                executed_at_type_0 = datetime.datetime.fromisoformat(data)

                return executed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        executed_at = _parse_executed_at(d.pop("executed_at", UNSET))

        requires_approval = d.pop("requires_approval", UNSET)

        def _parse_result(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        result = _parse_result(d.pop("result", UNSET))

        status = d.pop("status", UNSET)

        remediation_step = cls(
            action=action,
            order=order,
            risk=risk,
            command=command,
            executed_at=executed_at,
            requires_approval=requires_approval,
            result=result,
            status=status,
        )

        remediation_step.additional_properties = d
        return remediation_step

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
