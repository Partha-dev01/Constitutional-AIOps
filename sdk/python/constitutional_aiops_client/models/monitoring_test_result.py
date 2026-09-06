from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.probe_result import ProbeResult


T = TypeVar("T", bound="MonitoringTestResult")


@_attrs_define
class MonitoringTestResult:
    """Per-source result; a source is absent when it was not requested.

    Attributes:
        docker (None | ProbeResult | Unset):
        loki (None | ProbeResult | Unset):
        prometheus (None | ProbeResult | Unset):
        tempo (None | ProbeResult | Unset):
    """

    docker: None | ProbeResult | Unset = UNSET
    loki: None | ProbeResult | Unset = UNSET
    prometheus: None | ProbeResult | Unset = UNSET
    tempo: None | ProbeResult | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.probe_result import ProbeResult  # noqa: PLC0415

        docker: dict[str, Any] | None | Unset
        if isinstance(self.docker, Unset):
            docker = UNSET
        elif isinstance(self.docker, ProbeResult):
            docker = self.docker.to_dict()
        else:
            docker = self.docker

        loki: dict[str, Any] | None | Unset
        if isinstance(self.loki, Unset):
            loki = UNSET
        elif isinstance(self.loki, ProbeResult):
            loki = self.loki.to_dict()
        else:
            loki = self.loki

        prometheus: dict[str, Any] | None | Unset
        if isinstance(self.prometheus, Unset):
            prometheus = UNSET
        elif isinstance(self.prometheus, ProbeResult):
            prometheus = self.prometheus.to_dict()
        else:
            prometheus = self.prometheus

        tempo: dict[str, Any] | None | Unset
        if isinstance(self.tempo, Unset):
            tempo = UNSET
        elif isinstance(self.tempo, ProbeResult):
            tempo = self.tempo.to_dict()
        else:
            tempo = self.tempo

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if docker is not UNSET:
            field_dict["docker"] = docker
        if loki is not UNSET:
            field_dict["loki"] = loki
        if prometheus is not UNSET:
            field_dict["prometheus"] = prometheus
        if tempo is not UNSET:
            field_dict["tempo"] = tempo

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.probe_result import ProbeResult  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_docker(data: object) -> None | ProbeResult | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                docker_type_0 = ProbeResult.from_dict(data)

                return docker_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProbeResult | Unset, data)

        docker = _parse_docker(d.pop("docker", UNSET))

        def _parse_loki(data: object) -> None | ProbeResult | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                loki_type_0 = ProbeResult.from_dict(data)

                return loki_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProbeResult | Unset, data)

        loki = _parse_loki(d.pop("loki", UNSET))

        def _parse_prometheus(data: object) -> None | ProbeResult | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                prometheus_type_0 = ProbeResult.from_dict(data)

                return prometheus_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProbeResult | Unset, data)

        prometheus = _parse_prometheus(d.pop("prometheus", UNSET))

        def _parse_tempo(data: object) -> None | ProbeResult | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tempo_type_0 = ProbeResult.from_dict(data)

                return tempo_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProbeResult | Unset, data)

        tempo = _parse_tempo(d.pop("tempo", UNSET))

        monitoring_test_result = cls(
            docker=docker,
            loki=loki,
            prometheus=prometheus,
            tempo=tempo,
        )

        monitoring_test_result.additional_properties = d
        return monitoring_test_result

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
