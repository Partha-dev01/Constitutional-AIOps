from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.topology_episode import TopologyEpisode
    from ..models.topology_node_meta import TopologyNodeMeta


T = TypeVar("T", bound="TopologyNode")


@_attrs_define
class TopologyNode:
    """A platform service (or dynamic edge host) in the schema graph.

    Attributes:
        buckets (list[int]): Per-bucket episode counts, oldest → newest
        id (str):
        kind (str):
        label (str):
        tier (int):
        episode_count (int | Unset):  Default: 0.
        health (str | Unset): healthy | warning | critical | unknown Default: 'unknown'.
        health_reason (str | Unset):  Default: ''.
        incident_count (int | Unset): error/critical episodes in window Default: 0.
        last_episode_at (None | str | Unset):
        meta (TopologyNodeMeta | Unset): Static metadata for a topology node.
        recent_episodes (list[TopologyEpisode] | Unset):
    """

    buckets: list[int]
    id: str
    kind: str
    label: str
    tier: int
    episode_count: int | Unset = 0
    health: str | Unset = "unknown"
    health_reason: str | Unset = ""
    incident_count: int | Unset = 0
    last_episode_at: None | str | Unset = UNSET
    meta: TopologyNodeMeta | Unset = UNSET
    recent_episodes: list[TopologyEpisode] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        buckets = self.buckets

        id = self.id

        kind = self.kind

        label = self.label

        tier = self.tier

        episode_count = self.episode_count

        health = self.health

        health_reason = self.health_reason

        incident_count = self.incident_count

        last_episode_at: None | str | Unset
        if isinstance(self.last_episode_at, Unset):
            last_episode_at = UNSET
        else:
            last_episode_at = self.last_episode_at

        meta: dict[str, Any] | Unset = UNSET
        if not isinstance(self.meta, Unset):
            meta = self.meta.to_dict()

        recent_episodes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.recent_episodes, Unset):
            recent_episodes = []
            for recent_episodes_item_data in self.recent_episodes:
                recent_episodes_item = recent_episodes_item_data.to_dict()
                recent_episodes.append(recent_episodes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "buckets": buckets,
                "id": id,
                "kind": kind,
                "label": label,
                "tier": tier,
            }
        )
        if episode_count is not UNSET:
            field_dict["episode_count"] = episode_count
        if health is not UNSET:
            field_dict["health"] = health
        if health_reason is not UNSET:
            field_dict["health_reason"] = health_reason
        if incident_count is not UNSET:
            field_dict["incident_count"] = incident_count
        if last_episode_at is not UNSET:
            field_dict["last_episode_at"] = last_episode_at
        if meta is not UNSET:
            field_dict["meta"] = meta
        if recent_episodes is not UNSET:
            field_dict["recent_episodes"] = recent_episodes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.topology_episode import TopologyEpisode  # noqa: PLC0415
        from ..models.topology_node_meta import TopologyNodeMeta  # noqa: PLC0415

        d = dict(src_dict)
        buckets = cast(list[int], d.pop("buckets"))

        id = d.pop("id")

        kind = d.pop("kind")

        label = d.pop("label")

        tier = d.pop("tier")

        episode_count = d.pop("episode_count", UNSET)

        health = d.pop("health", UNSET)

        health_reason = d.pop("health_reason", UNSET)

        incident_count = d.pop("incident_count", UNSET)

        def _parse_last_episode_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_episode_at = _parse_last_episode_at(d.pop("last_episode_at", UNSET))

        _meta = d.pop("meta", UNSET)
        meta: TopologyNodeMeta | Unset
        if isinstance(_meta, Unset):
            meta = UNSET
        else:
            meta = TopologyNodeMeta.from_dict(_meta)

        _recent_episodes = d.pop("recent_episodes", UNSET)
        recent_episodes: list[TopologyEpisode] | Unset = UNSET
        if _recent_episodes is not UNSET:
            recent_episodes = []
            for recent_episodes_item_data in _recent_episodes:
                recent_episodes_item = TopologyEpisode.from_dict(
                    recent_episodes_item_data
                )

                recent_episodes.append(recent_episodes_item)

        topology_node = cls(
            buckets=buckets,
            id=id,
            kind=kind,
            label=label,
            tier=tier,
            episode_count=episode_count,
            health=health,
            health_reason=health_reason,
            incident_count=incident_count,
            last_episode_at=last_episode_at,
            meta=meta,
            recent_episodes=recent_episodes,
        )

        topology_node.additional_properties = d
        return topology_node

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
