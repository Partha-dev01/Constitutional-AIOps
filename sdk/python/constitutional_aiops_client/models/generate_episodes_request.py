from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GenerateEpisodesRequest")


@_attrs_define
class GenerateEpisodesRequest:
    """Request to generate demo episodes via Reasoning Agent.

    Attributes:
        clear_existing (bool | Unset): Clear existing graph data before generating. Defaults to False: wiping the whole
            graph (MATCH (n) DETACH DELETE n) must be an explicit opt-in, never the effect of a bare POST. Default: False.
        count_per_service (int | Unset): Number of episodes per service (1-3) Default: 1.
        services (list[str] | None | Unset): Specific services to generate episodes for. If None, generates for all.
    """

    clear_existing: bool | Unset = False
    count_per_service: int | Unset = 1
    services: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        clear_existing = self.clear_existing

        count_per_service = self.count_per_service

        services: list[str] | None | Unset
        if isinstance(self.services, Unset):
            services = UNSET
        elif isinstance(self.services, list):
            services = self.services

        else:
            services = self.services

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if clear_existing is not UNSET:
            field_dict["clear_existing"] = clear_existing
        if count_per_service is not UNSET:
            field_dict["count_per_service"] = count_per_service
        if services is not UNSET:
            field_dict["services"] = services

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        clear_existing = d.pop("clear_existing", UNSET)

        count_per_service = d.pop("count_per_service", UNSET)

        def _parse_services(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                services_type_0 = cast(list[str], data)

                return services_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        services = _parse_services(d.pop("services", UNSET))

        generate_episodes_request = cls(
            clear_existing=clear_existing,
            count_per_service=count_per_service,
            services=services,
        )

        generate_episodes_request.additional_properties = d
        return generate_episodes_request

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
