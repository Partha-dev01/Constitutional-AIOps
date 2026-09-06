from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceSpan")


@_attrs_define
class TraceSpan:
    """Trace span from Tempo.

    Attributes:
        duration_ms (float):
        operation (str):
        service (str):
        span_id (str):
        status (str):
        trace_id (str):
        parent_span_id (None | str | Unset):
    """

    duration_ms: float
    operation: str
    service: str
    span_id: str
    status: str
    trace_id: str
    parent_span_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        duration_ms = self.duration_ms

        operation = self.operation

        service = self.service

        span_id = self.span_id

        status = self.status

        trace_id = self.trace_id

        parent_span_id: None | str | Unset
        if isinstance(self.parent_span_id, Unset):
            parent_span_id = UNSET
        else:
            parent_span_id = self.parent_span_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "duration_ms": duration_ms,
                "operation": operation,
                "service": service,
                "span_id": span_id,
                "status": status,
                "trace_id": trace_id,
            }
        )
        if parent_span_id is not UNSET:
            field_dict["parent_span_id"] = parent_span_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        duration_ms = d.pop("duration_ms")

        operation = d.pop("operation")

        service = d.pop("service")

        span_id = d.pop("span_id")

        status = d.pop("status")

        trace_id = d.pop("trace_id")

        def _parse_parent_span_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_span_id = _parse_parent_span_id(d.pop("parent_span_id", UNSET))

        trace_span = cls(
            duration_ms=duration_ms,
            operation=operation,
            service=service,
            span_id=span_id,
            status=status,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )

        trace_span.additional_properties = d
        return trace_span

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
