from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TelemetrySettingsModel")


@_attrs_define
class TelemetrySettingsModel:
    """
    Attributes:
        docker_enabled (bool | Unset):  Default: True.
        loki_enabled (bool | Unset):  Default: True.
        loki_url (str | Unset):  Default: 'http://loki:3100'.
        prometheus_enabled (bool | Unset):  Default: True.
        prometheus_url (str | Unset):  Default: 'http://prometheus:9090'.
        retention_days (int | Unset):  Default: 30.
        tempo_enabled (bool | Unset):  Default: True.
        tempo_url (str | Unset):  Default: 'http://tempo:3200'.
    """

    docker_enabled: bool | Unset = True
    loki_enabled: bool | Unset = True
    loki_url: str | Unset = "http://loki:3100"
    prometheus_enabled: bool | Unset = True
    prometheus_url: str | Unset = "http://prometheus:9090"
    retention_days: int | Unset = 30
    tempo_enabled: bool | Unset = True
    tempo_url: str | Unset = "http://tempo:3200"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        docker_enabled = self.docker_enabled

        loki_enabled = self.loki_enabled

        loki_url = self.loki_url

        prometheus_enabled = self.prometheus_enabled

        prometheus_url = self.prometheus_url

        retention_days = self.retention_days

        tempo_enabled = self.tempo_enabled

        tempo_url = self.tempo_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if docker_enabled is not UNSET:
            field_dict["dockerEnabled"] = docker_enabled
        if loki_enabled is not UNSET:
            field_dict["lokiEnabled"] = loki_enabled
        if loki_url is not UNSET:
            field_dict["lokiUrl"] = loki_url
        if prometheus_enabled is not UNSET:
            field_dict["prometheusEnabled"] = prometheus_enabled
        if prometheus_url is not UNSET:
            field_dict["prometheusUrl"] = prometheus_url
        if retention_days is not UNSET:
            field_dict["retentionDays"] = retention_days
        if tempo_enabled is not UNSET:
            field_dict["tempoEnabled"] = tempo_enabled
        if tempo_url is not UNSET:
            field_dict["tempoUrl"] = tempo_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        docker_enabled = d.pop("dockerEnabled", UNSET)

        loki_enabled = d.pop("lokiEnabled", UNSET)

        loki_url = d.pop("lokiUrl", UNSET)

        prometheus_enabled = d.pop("prometheusEnabled", UNSET)

        prometheus_url = d.pop("prometheusUrl", UNSET)

        retention_days = d.pop("retentionDays", UNSET)

        tempo_enabled = d.pop("tempoEnabled", UNSET)

        tempo_url = d.pop("tempoUrl", UNSET)

        telemetry_settings_model = cls(
            docker_enabled=docker_enabled,
            loki_enabled=loki_enabled,
            loki_url=loki_url,
            prometheus_enabled=prometheus_enabled,
            prometheus_url=prometheus_url,
            retention_days=retention_days,
            tempo_enabled=tempo_enabled,
            tempo_url=tempo_url,
        )

        telemetry_settings_model.additional_properties = d
        return telemetry_settings_model

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
