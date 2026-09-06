from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ActionExecutionResult")


@_attrs_define
class ActionExecutionResult:
    """Result of action execution.

    Example:
        {'completed_at': '2025-12-14T10:32:45Z', 'duration_ms': 45000, 'output': 'Service restarted successfully. New
            pod: payment-service-xyz789', 'rollback_available': True, 'started_at': '2025-12-14T10:32:00Z', 'success': True}

    Attributes:
        completed_at (datetime.datetime):
        duration_ms (float):
        started_at (datetime.datetime):
        success (bool):
        error (None | str | Unset):
        output (None | str | Unset):
        rollback_available (bool | Unset):  Default: False.
    """

    completed_at: datetime.datetime
    duration_ms: float
    started_at: datetime.datetime
    success: bool
    error: None | str | Unset = UNSET
    output: None | str | Unset = UNSET
    rollback_available: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        completed_at = self.completed_at.isoformat()

        duration_ms = self.duration_ms

        started_at = self.started_at.isoformat()

        success = self.success

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        output: None | str | Unset
        if isinstance(self.output, Unset):
            output = UNSET
        else:
            output = self.output

        rollback_available = self.rollback_available

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "completed_at": completed_at,
                "duration_ms": duration_ms,
                "started_at": started_at,
                "success": success,
            }
        )
        if error is not UNSET:
            field_dict["error"] = error
        if output is not UNSET:
            field_dict["output"] = output
        if rollback_available is not UNSET:
            field_dict["rollback_available"] = rollback_available

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        completed_at = datetime.datetime.fromisoformat(d.pop("completed_at"))

        duration_ms = d.pop("duration_ms")

        started_at = datetime.datetime.fromisoformat(d.pop("started_at"))

        success = d.pop("success")

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_output(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output = _parse_output(d.pop("output", UNSET))

        rollback_available = d.pop("rollback_available", UNSET)

        action_execution_result = cls(
            completed_at=completed_at,
            duration_ms=duration_ms,
            started_at=started_at,
            success=success,
            error=error,
            output=output,
            rollback_available=rollback_available,
        )

        action_execution_result.additional_properties = d
        return action_execution_result

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
