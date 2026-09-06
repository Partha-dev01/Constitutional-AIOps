from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.episode import Episode


T = TypeVar("T", bound="SimilarEpisode")


@_attrs_define
class SimilarEpisode:
    """Similar episode from memory search.

    Attributes:
        episode (Episode): Episode from episodic memory (legacy).
        similarity_score (float):
    """

    episode: Episode
    similarity_score: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        episode = self.episode.to_dict()

        similarity_score = self.similarity_score

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "episode": episode,
                "similarity_score": similarity_score,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.episode import Episode  # noqa: PLC0415

        d = dict(src_dict)
        episode = Episode.from_dict(d.pop("episode"))

        similarity_score = d.pop("similarity_score")

        similar_episode = cls(
            episode=episode,
            similarity_score=similarity_score,
        )

        similar_episode.additional_properties = d
        return similar_episode

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
