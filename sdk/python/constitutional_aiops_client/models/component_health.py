from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.component_health_details_type_0 import ComponentHealthDetailsType0


T = TypeVar("T", bound="ComponentHealth")


@_attrs_define
class ComponentHealth:
    """Health status of a single component.

    Attributes:
        healthy (bool):
        name (str):
        details (ComponentHealthDetailsType0 | None | Unset):
        error (None | str | Unset):
        latency_ms (float | None | Unset):
    """

    healthy: bool
    name: str
    details: ComponentHealthDetailsType0 | None | Unset = UNSET
    error: None | str | Unset = UNSET
    latency_ms: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.component_health_details_type_0 import (
            ComponentHealthDetailsType0,  # noqa: PLC0415
        )

        healthy = self.healthy

        name = self.name

        details: dict[str, Any] | None | Unset
        if isinstance(self.details, Unset):
            details = UNSET
        elif isinstance(self.details, ComponentHealthDetailsType0):
            details = self.details.to_dict()
        else:
            details = self.details

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        latency_ms: float | None | Unset
        if isinstance(self.latency_ms, Unset):
            latency_ms = UNSET
        else:
            latency_ms = self.latency_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "healthy": healthy,
                "name": name,
            }
        )
        if details is not UNSET:
            field_dict["details"] = details
        if error is not UNSET:
            field_dict["error"] = error
        if latency_ms is not UNSET:
            field_dict["latency_ms"] = latency_ms

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.component_health_details_type_0 import (
            ComponentHealthDetailsType0,  # noqa: PLC0415
        )

        d = dict(src_dict)
        healthy = d.pop("healthy")

        name = d.pop("name")

        def _parse_details(data: object) -> ComponentHealthDetailsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                details_type_0 = ComponentHealthDetailsType0.from_dict(data)

                return details_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ComponentHealthDetailsType0 | None | Unset, data)

        details = _parse_details(d.pop("details", UNSET))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_latency_ms(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        latency_ms = _parse_latency_ms(d.pop("latency_ms", UNSET))

        component_health = cls(
            healthy=healthy,
            name=name,
            details=details,
            error=error,
            latency_ms=latency_ms,
        )

        component_health.additional_properties = d
        return component_health

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
