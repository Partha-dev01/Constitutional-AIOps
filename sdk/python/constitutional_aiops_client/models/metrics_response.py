from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.metric_point import MetricPoint


T = TypeVar("T", bound="MetricsResponse")


@_attrs_define
class MetricsResponse:
    """Response containing metrics. ``source`` names where the data came from
    (``loki``/``prometheus``, ``docker`` fallback, or ``none``) so the UI can
    show honest, source-aware empty states.

        Attributes:
            metrics (list[MetricPoint]):
            range_ (str):
            step (str):
            source (str | Unset):  Default: 'prometheus'.
    """

    metrics: list[MetricPoint]
    range_: str
    step: str
    source: str | Unset = "prometheus"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metrics = []
        for metrics_item_data in self.metrics:
            metrics_item = metrics_item_data.to_dict()
            metrics.append(metrics_item)

        range_ = self.range_

        step = self.step

        source = self.source

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metrics": metrics,
                "range": range_,
                "step": step,
            }
        )
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metric_point import MetricPoint  # noqa: PLC0415

        d = dict(src_dict)
        metrics = []
        _metrics = d.pop("metrics")
        for metrics_item_data in _metrics:
            metrics_item = MetricPoint.from_dict(metrics_item_data)

            metrics.append(metrics_item)

        range_ = d.pop("range")

        step = d.pop("step")

        source = d.pop("source", UNSET)

        metrics_response = cls(
            metrics=metrics,
            range_=range_,
            step=step,
            source=source,
        )

        metrics_response.additional_properties = d
        return metrics_response

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
