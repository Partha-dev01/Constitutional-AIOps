from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.trace_span import TraceSpan


T = TypeVar("T", bound="TracesResponse")


@_attrs_define
class TracesResponse:
    """Response containing traces.

    Attributes:
        total (int):
        traces (list[TraceSpan]):
    """

    total: int
    traces: list[TraceSpan]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total = self.total

        traces = []
        for traces_item_data in self.traces:
            traces_item = traces_item_data.to_dict()
            traces.append(traces_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "traces": traces,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_span import TraceSpan  # noqa: PLC0415

        d = dict(src_dict)
        total = d.pop("total")

        traces = []
        _traces = d.pop("traces")
        for traces_item_data in _traces:
            traces_item = TraceSpan.from_dict(traces_item_data)

            traces.append(traces_item)

        traces_response = cls(
            total=total,
            traces=traces,
        )

        traces_response.additional_properties = d
        return traces_response

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
