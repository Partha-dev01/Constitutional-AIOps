from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BenchmarkRequest")


@_attrs_define
class BenchmarkRequest:
    """Request to start a benchmark.

    Attributes:
        max_annotation_tests (int | Unset):  Default: 100.
        max_rca_tests (int | Unset):  Default: 50.
        model_name (str | Unset):  Default: 'constitutional_aiops'.
        temperature (float | Unset):  Default: 0.0.
        timeout_seconds (int | Unset):  Default: 300.
    """

    max_annotation_tests: int | Unset = 100
    max_rca_tests: int | Unset = 50
    model_name: str | Unset = "constitutional_aiops"
    temperature: float | Unset = 0.0
    timeout_seconds: int | Unset = 300
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        max_annotation_tests = self.max_annotation_tests

        max_rca_tests = self.max_rca_tests

        model_name = self.model_name

        temperature = self.temperature

        timeout_seconds = self.timeout_seconds

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if max_annotation_tests is not UNSET:
            field_dict["max_annotation_tests"] = max_annotation_tests
        if max_rca_tests is not UNSET:
            field_dict["max_rca_tests"] = max_rca_tests
        if model_name is not UNSET:
            field_dict["model_name"] = model_name
        if temperature is not UNSET:
            field_dict["temperature"] = temperature
        if timeout_seconds is not UNSET:
            field_dict["timeout_seconds"] = timeout_seconds

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        max_annotation_tests = d.pop("max_annotation_tests", UNSET)

        max_rca_tests = d.pop("max_rca_tests", UNSET)

        model_name = d.pop("model_name", UNSET)

        temperature = d.pop("temperature", UNSET)

        timeout_seconds = d.pop("timeout_seconds", UNSET)

        benchmark_request = cls(
            max_annotation_tests=max_annotation_tests,
            max_rca_tests=max_rca_tests,
            model_name=model_name,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
        )

        benchmark_request.additional_properties = d
        return benchmark_request

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
