from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GraphStatsResponse")


@_attrs_define
class GraphStatsResponse:
    """Graph database statistics.

    Attributes:
        connected (bool):
        edge_count (int):
        episode_count (int):
        node_count (int):
    """

    connected: bool
    edge_count: int
    episode_count: int
    node_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        connected = self.connected

        edge_count = self.edge_count

        episode_count = self.episode_count

        node_count = self.node_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "connected": connected,
                "edge_count": edge_count,
                "episode_count": episode_count,
                "node_count": node_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        connected = d.pop("connected")

        edge_count = d.pop("edge_count")

        episode_count = d.pop("episode_count")

        node_count = d.pop("node_count")

        graph_stats_response = cls(
            connected=connected,
            edge_count=edge_count,
            episode_count=episode_count,
            node_count=node_count,
        )

        graph_stats_response.additional_properties = d
        return graph_stats_response

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
