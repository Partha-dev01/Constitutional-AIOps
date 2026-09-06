from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DependencyGraph")


@_attrs_define
class DependencyGraph:
    """Service dependency graph.

    Attributes:
        depth (int):
        downstream (list[str]):
        service (str):
        upstream (list[str]):
    """

    depth: int
    downstream: list[str]
    service: str
    upstream: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        depth = self.depth

        downstream = self.downstream

        service = self.service

        upstream = self.upstream

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "depth": depth,
                "downstream": downstream,
                "service": service,
                "upstream": upstream,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        depth = d.pop("depth")

        downstream = cast(list[str], d.pop("downstream"))

        service = d.pop("service")

        upstream = cast(list[str], d.pop("upstream"))

        dependency_graph = cls(
            depth=depth,
            downstream=downstream,
            service=service,
            upstream=upstream,
        )

        dependency_graph.additional_properties = d
        return dependency_graph

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
