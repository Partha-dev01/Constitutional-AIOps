from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AgentStats")


@_attrs_define
class AgentStats:
    """Agent statistics.

    Attributes:
        avg_latency_ms (float):
        error_count (int):
        requests_per_minute (float):
        success_count (int):
        total_requests (int):
    """

    avg_latency_ms: float
    error_count: int
    requests_per_minute: float
    success_count: int
    total_requests: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        avg_latency_ms = self.avg_latency_ms

        error_count = self.error_count

        requests_per_minute = self.requests_per_minute

        success_count = self.success_count

        total_requests = self.total_requests

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "avg_latency_ms": avg_latency_ms,
                "error_count": error_count,
                "requests_per_minute": requests_per_minute,
                "success_count": success_count,
                "total_requests": total_requests,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        avg_latency_ms = d.pop("avg_latency_ms")

        error_count = d.pop("error_count")

        requests_per_minute = d.pop("requests_per_minute")

        success_count = d.pop("success_count")

        total_requests = d.pop("total_requests")

        agent_stats = cls(
            avg_latency_ms=avg_latency_ms,
            error_count=error_count,
            requests_per_minute=requests_per_minute,
            success_count=success_count,
            total_requests=total_requests,
        )

        agent_stats.additional_properties = d
        return agent_stats

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
