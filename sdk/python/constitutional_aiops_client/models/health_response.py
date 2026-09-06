from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.component_health import ComponentHealth


T = TypeVar("T", bound="HealthResponse")


@_attrs_define
class HealthResponse:
    """Overall system health response.

    Example:
        {'components': [{'healthy': True, 'latency_ms': 15.2, 'name': 'fast_agent'}, {'healthy': True, 'latency_ms':
            45.8, 'name': 'reasoning_agent'}, {'healthy': True, 'latency_ms': 8.1, 'name': 'neo4j'}], 'status': 'healthy',
            'timestamp': '2025-12-14T10:00:00Z', 'uptime_seconds': 3600.5, 'version': '0.1.0'}

    Attributes:
        components (list[ComponentHealth]):
        status (str): Overall status: healthy, degraded, unhealthy
        timestamp (datetime.datetime):
        version (str):
        uptime_seconds (float | None | Unset):
    """

    components: list[ComponentHealth]
    status: str
    timestamp: datetime.datetime
    version: str
    uptime_seconds: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        components = []
        for components_item_data in self.components:
            components_item = components_item_data.to_dict()
            components.append(components_item)

        status = self.status

        timestamp = self.timestamp.isoformat()

        version = self.version

        uptime_seconds: float | None | Unset
        if isinstance(self.uptime_seconds, Unset):
            uptime_seconds = UNSET
        else:
            uptime_seconds = self.uptime_seconds

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "components": components,
                "status": status,
                "timestamp": timestamp,
                "version": version,
            }
        )
        if uptime_seconds is not UNSET:
            field_dict["uptime_seconds"] = uptime_seconds

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.component_health import ComponentHealth  # noqa: PLC0415

        d = dict(src_dict)
        components = []
        _components = d.pop("components")
        for components_item_data in _components:
            components_item = ComponentHealth.from_dict(components_item_data)

            components.append(components_item)

        status = d.pop("status")

        timestamp = datetime.datetime.fromisoformat(d.pop("timestamp"))

        version = d.pop("version")

        def _parse_uptime_seconds(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        uptime_seconds = _parse_uptime_seconds(d.pop("uptime_seconds", UNSET))

        health_response = cls(
            components=components,
            status=status,
            timestamp=timestamp,
            version=version,
            uptime_seconds=uptime_seconds,
        )

        health_response.additional_properties = d
        return health_response

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
