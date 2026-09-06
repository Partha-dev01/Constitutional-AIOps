from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.latency_stats import LatencyStats
    from ..models.metrics_snapshot_determinism_config import (
        MetricsSnapshotDeterminismConfig,
    )


T = TypeVar("T", bound="MetricsSnapshot")


@_attrs_define
class MetricsSnapshot:
    """Complete metrics snapshot.

    Attributes:
        fast_agent (LatencyStats): Latency statistics for an agent.
        reasoning_agent (LatencyStats): Latency statistics for an agent.
        success_rate (float):
        timestamp (str):
        total_requests (int):
        determinism_config (MetricsSnapshotDeterminismConfig | Unset):
    """

    fast_agent: LatencyStats
    reasoning_agent: LatencyStats
    success_rate: float
    timestamp: str
    total_requests: int
    determinism_config: MetricsSnapshotDeterminismConfig | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fast_agent = self.fast_agent.to_dict()

        reasoning_agent = self.reasoning_agent.to_dict()

        success_rate = self.success_rate

        timestamp = self.timestamp

        total_requests = self.total_requests

        determinism_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.determinism_config, Unset):
            determinism_config = self.determinism_config.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "fast_agent": fast_agent,
                "reasoning_agent": reasoning_agent,
                "success_rate": success_rate,
                "timestamp": timestamp,
                "total_requests": total_requests,
            }
        )
        if determinism_config is not UNSET:
            field_dict["determinism_config"] = determinism_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.latency_stats import LatencyStats  # noqa: PLC0415
        from ..models.metrics_snapshot_determinism_config import (
            MetricsSnapshotDeterminismConfig,  # noqa: PLC0415
        )

        d = dict(src_dict)
        fast_agent = LatencyStats.from_dict(d.pop("fast_agent"))

        reasoning_agent = LatencyStats.from_dict(d.pop("reasoning_agent"))

        success_rate = d.pop("success_rate")

        timestamp = d.pop("timestamp")

        total_requests = d.pop("total_requests")

        _determinism_config = d.pop("determinism_config", UNSET)
        determinism_config: MetricsSnapshotDeterminismConfig | Unset
        if isinstance(_determinism_config, Unset):
            determinism_config = UNSET
        else:
            determinism_config = MetricsSnapshotDeterminismConfig.from_dict(
                _determinism_config
            )

        metrics_snapshot = cls(
            fast_agent=fast_agent,
            reasoning_agent=reasoning_agent,
            success_rate=success_rate,
            timestamp=timestamp,
            total_requests=total_requests,
            determinism_config=determinism_config,
        )

        metrics_snapshot.additional_properties = d
        return metrics_snapshot

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
