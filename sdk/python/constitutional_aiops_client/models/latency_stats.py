from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LatencyStats")


@_attrs_define
class LatencyStats:
    """Latency statistics for an agent.

    Attributes:
        avg_ms (float):
        count (int):
        max_ms (float):
        min_ms (float):
        p50_ms (float):
        p95_ms (float):
        p99_ms (float):
        success_rate (float):
        total_tokens (int | Unset):  Default: 0.
    """

    avg_ms: float
    count: int
    max_ms: float
    min_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    success_rate: float
    total_tokens: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        avg_ms = self.avg_ms

        count = self.count

        max_ms = self.max_ms

        min_ms = self.min_ms

        p50_ms = self.p50_ms

        p95_ms = self.p95_ms

        p99_ms = self.p99_ms

        success_rate = self.success_rate

        total_tokens = self.total_tokens

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "avg_ms": avg_ms,
                "count": count,
                "max_ms": max_ms,
                "min_ms": min_ms,
                "p50_ms": p50_ms,
                "p95_ms": p95_ms,
                "p99_ms": p99_ms,
                "success_rate": success_rate,
            }
        )
        if total_tokens is not UNSET:
            field_dict["total_tokens"] = total_tokens

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        avg_ms = d.pop("avg_ms")

        count = d.pop("count")

        max_ms = d.pop("max_ms")

        min_ms = d.pop("min_ms")

        p50_ms = d.pop("p50_ms")

        p95_ms = d.pop("p95_ms")

        p99_ms = d.pop("p99_ms")

        success_rate = d.pop("success_rate")

        total_tokens = d.pop("total_tokens", UNSET)

        latency_stats = cls(
            avg_ms=avg_ms,
            count=count,
            max_ms=max_ms,
            min_ms=min_ms,
            p50_ms=p50_ms,
            p95_ms=p95_ms,
            p99_ms=p99_ms,
            success_rate=success_rate,
            total_tokens=total_tokens,
        )

        latency_stats.additional_properties = d
        return latency_stats

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
