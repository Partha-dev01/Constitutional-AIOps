from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.agent_activity import AgentActivity


T = TypeVar("T", bound="ActivityListResponse")


@_attrs_define
class ActivityListResponse:
    """Response listing agent activities.

    Attributes:
        activities (list[AgentActivity]):
        agent_type (str):
        total (int):
    """

    activities: list[AgentActivity]
    agent_type: str
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        activities = []
        for activities_item_data in self.activities:
            activities_item = activities_item_data.to_dict()
            activities.append(activities_item)

        agent_type = self.agent_type

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "activities": activities,
                "agent_type": agent_type,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_activity import AgentActivity  # noqa: PLC0415

        d = dict(src_dict)
        activities = []
        _activities = d.pop("activities")
        for activities_item_data in _activities:
            activities_item = AgentActivity.from_dict(activities_item_data)

            activities.append(activities_item)

        agent_type = d.pop("agent_type")

        total = d.pop("total")

        activity_list_response = cls(
            activities=activities,
            agent_type=agent_type,
            total=total,
        )

        activity_list_response.additional_properties = d
        return activity_list_response

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
