from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MonitoringTestRequest")


@_attrs_define
class MonitoringTestRequest:
    """Monitoring sources to probe. URLs: any subset (blanks are skipped). The
    local Docker socket has no URL, so a ``docker=true`` flag requests it.

        Attributes:
            docker (bool | None | Unset):
            loki_url (None | str | Unset):
            prometheus_url (None | str | Unset):
            tempo_url (None | str | Unset):
    """

    docker: bool | None | Unset = UNSET
    loki_url: None | str | Unset = UNSET
    prometheus_url: None | str | Unset = UNSET
    tempo_url: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        docker: bool | None | Unset
        if isinstance(self.docker, Unset):
            docker = UNSET
        else:
            docker = self.docker

        loki_url: None | str | Unset
        if isinstance(self.loki_url, Unset):
            loki_url = UNSET
        else:
            loki_url = self.loki_url

        prometheus_url: None | str | Unset
        if isinstance(self.prometheus_url, Unset):
            prometheus_url = UNSET
        else:
            prometheus_url = self.prometheus_url

        tempo_url: None | str | Unset
        if isinstance(self.tempo_url, Unset):
            tempo_url = UNSET
        else:
            tempo_url = self.tempo_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if docker is not UNSET:
            field_dict["docker"] = docker
        if loki_url is not UNSET:
            field_dict["lokiUrl"] = loki_url
        if prometheus_url is not UNSET:
            field_dict["prometheusUrl"] = prometheus_url
        if tempo_url is not UNSET:
            field_dict["tempoUrl"] = tempo_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_docker(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        docker = _parse_docker(d.pop("docker", UNSET))

        def _parse_loki_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        loki_url = _parse_loki_url(d.pop("lokiUrl", UNSET))

        def _parse_prometheus_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        prometheus_url = _parse_prometheus_url(d.pop("prometheusUrl", UNSET))

        def _parse_tempo_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tempo_url = _parse_tempo_url(d.pop("tempoUrl", UNSET))

        monitoring_test_request = cls(
            docker=docker,
            loki_url=loki_url,
            prometheus_url=prometheus_url,
            tempo_url=tempo_url,
        )

        monitoring_test_request.additional_properties = d
        return monitoring_test_request

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
