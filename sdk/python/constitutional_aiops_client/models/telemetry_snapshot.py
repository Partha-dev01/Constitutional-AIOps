from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.telemetry_snapshot_metrics_type_0 import TelemetrySnapshotMetricsType0


T = TypeVar("T", bound="TelemetrySnapshot")


@_attrs_define
class TelemetrySnapshot:
    """Telemetry data at time of incident.

    Attributes:
        compressed_context (None | str | Unset): Token-compressed telemetry summary
        logs (list[str] | None | Unset): Relevant log entries
        metrics (None | TelemetrySnapshotMetricsType0 | Unset): Key metrics
        traces (list[str] | None | Unset): Trace IDs
    """

    compressed_context: None | str | Unset = UNSET
    logs: list[str] | None | Unset = UNSET
    metrics: None | TelemetrySnapshotMetricsType0 | Unset = UNSET
    traces: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.telemetry_snapshot_metrics_type_0 import (
            TelemetrySnapshotMetricsType0,  # noqa: PLC0415
        )

        compressed_context: None | str | Unset
        if isinstance(self.compressed_context, Unset):
            compressed_context = UNSET
        else:
            compressed_context = self.compressed_context

        logs: list[str] | None | Unset
        if isinstance(self.logs, Unset):
            logs = UNSET
        elif isinstance(self.logs, list):
            logs = self.logs

        else:
            logs = self.logs

        metrics: dict[str, Any] | None | Unset
        if isinstance(self.metrics, Unset):
            metrics = UNSET
        elif isinstance(self.metrics, TelemetrySnapshotMetricsType0):
            metrics = self.metrics.to_dict()
        else:
            metrics = self.metrics

        traces: list[str] | None | Unset
        if isinstance(self.traces, Unset):
            traces = UNSET
        elif isinstance(self.traces, list):
            traces = self.traces

        else:
            traces = self.traces

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if compressed_context is not UNSET:
            field_dict["compressed_context"] = compressed_context
        if logs is not UNSET:
            field_dict["logs"] = logs
        if metrics is not UNSET:
            field_dict["metrics"] = metrics
        if traces is not UNSET:
            field_dict["traces"] = traces

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.telemetry_snapshot_metrics_type_0 import (
            TelemetrySnapshotMetricsType0,  # noqa: PLC0415
        )

        d = dict(src_dict)

        def _parse_compressed_context(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        compressed_context = _parse_compressed_context(
            d.pop("compressed_context", UNSET)
        )

        def _parse_logs(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                logs_type_0 = cast(list[str], data)

                return logs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        logs = _parse_logs(d.pop("logs", UNSET))

        def _parse_metrics(
            data: object,
        ) -> None | TelemetrySnapshotMetricsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metrics_type_0 = TelemetrySnapshotMetricsType0.from_dict(data)

                return metrics_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TelemetrySnapshotMetricsType0 | Unset, data)

        metrics = _parse_metrics(d.pop("metrics", UNSET))

        def _parse_traces(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                traces_type_0 = cast(list[str], data)

                return traces_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        traces = _parse_traces(d.pop("traces", UNSET))

        telemetry_snapshot = cls(
            compressed_context=compressed_context,
            logs=logs,
            metrics=metrics,
            traces=traces,
        )

        telemetry_snapshot.additional_properties = d
        return telemetry_snapshot

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
