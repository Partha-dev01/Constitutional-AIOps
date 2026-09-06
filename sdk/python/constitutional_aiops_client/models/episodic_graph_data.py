from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action_node import ActionNode
    from ..models.entity_node import EntityNode
    from ..models.episode_node import EpisodeNode
    from ..models.episodic_graph_data_stats import EpisodicGraphDataStats
    from ..models.graph_edge import GraphEdge
    from ..models.root_cause_node import RootCauseNode
    from ..models.service_node import ServiceNode


T = TypeVar("T", bound="EpisodicGraphData")


@_attrs_define
class EpisodicGraphData:
    """Complete episodic memory graph for visualization.

    Attributes:
        actions (list[ActionNode]):
        edges (list[GraphEdge]):
        episodes (list[EpisodeNode]):
        root_causes (list[RootCauseNode]):
        services (list[ServiceNode]):
        entities (list[EntityNode] | Unset):
        stats (EpisodicGraphDataStats | Unset):
    """

    actions: list[ActionNode]
    edges: list[GraphEdge]
    episodes: list[EpisodeNode]
    root_causes: list[RootCauseNode]
    services: list[ServiceNode]
    entities: list[EntityNode] | Unset = UNSET
    stats: EpisodicGraphDataStats | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        actions = []
        for actions_item_data in self.actions:
            actions_item = actions_item_data.to_dict()
            actions.append(actions_item)

        edges = []
        for edges_item_data in self.edges:
            edges_item = edges_item_data.to_dict()
            edges.append(edges_item)

        episodes = []
        for episodes_item_data in self.episodes:
            episodes_item = episodes_item_data.to_dict()
            episodes.append(episodes_item)

        root_causes = []
        for root_causes_item_data in self.root_causes:
            root_causes_item = root_causes_item_data.to_dict()
            root_causes.append(root_causes_item)

        services = []
        for services_item_data in self.services:
            services_item = services_item_data.to_dict()
            services.append(services_item)

        entities: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.entities, Unset):
            entities = []
            for entities_item_data in self.entities:
                entities_item = entities_item_data.to_dict()
                entities.append(entities_item)

        stats: dict[str, Any] | Unset = UNSET
        if not isinstance(self.stats, Unset):
            stats = self.stats.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "actions": actions,
                "edges": edges,
                "episodes": episodes,
                "root_causes": root_causes,
                "services": services,
            }
        )
        if entities is not UNSET:
            field_dict["entities"] = entities
        if stats is not UNSET:
            field_dict["stats"] = stats

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action_node import ActionNode  # noqa: PLC0415
        from ..models.entity_node import EntityNode  # noqa: PLC0415
        from ..models.episode_node import EpisodeNode  # noqa: PLC0415
        from ..models.episodic_graph_data_stats import (
            EpisodicGraphDataStats,  # noqa: PLC0415
        )
        from ..models.graph_edge import GraphEdge  # noqa: PLC0415
        from ..models.root_cause_node import RootCauseNode  # noqa: PLC0415
        from ..models.service_node import ServiceNode  # noqa: PLC0415

        d = dict(src_dict)
        actions = []
        _actions = d.pop("actions")
        for actions_item_data in _actions:
            actions_item = ActionNode.from_dict(actions_item_data)

            actions.append(actions_item)

        edges = []
        _edges = d.pop("edges")
        for edges_item_data in _edges:
            edges_item = GraphEdge.from_dict(edges_item_data)

            edges.append(edges_item)

        episodes = []
        _episodes = d.pop("episodes")
        for episodes_item_data in _episodes:
            episodes_item = EpisodeNode.from_dict(episodes_item_data)

            episodes.append(episodes_item)

        root_causes = []
        _root_causes = d.pop("root_causes")
        for root_causes_item_data in _root_causes:
            root_causes_item = RootCauseNode.from_dict(root_causes_item_data)

            root_causes.append(root_causes_item)

        services = []
        _services = d.pop("services")
        for services_item_data in _services:
            services_item = ServiceNode.from_dict(services_item_data)

            services.append(services_item)

        _entities = d.pop("entities", UNSET)
        entities: list[EntityNode] | Unset = UNSET
        if _entities is not UNSET:
            entities = []
            for entities_item_data in _entities:
                entities_item = EntityNode.from_dict(entities_item_data)

                entities.append(entities_item)

        _stats = d.pop("stats", UNSET)
        stats: EpisodicGraphDataStats | Unset
        if isinstance(_stats, Unset):
            stats = UNSET
        else:
            stats = EpisodicGraphDataStats.from_dict(_stats)

        episodic_graph_data = cls(
            actions=actions,
            edges=edges,
            episodes=episodes,
            root_causes=root_causes,
            services=services,
            entities=entities,
            stats=stats,
        )

        episodic_graph_data.additional_properties = d
        return episodic_graph_data

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
