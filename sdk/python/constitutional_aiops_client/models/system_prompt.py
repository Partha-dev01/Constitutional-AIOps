from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SystemPrompt")


@_attrs_define
class SystemPrompt:
    """System prompt configuration.

    Attributes:
        agent (str): Agent: fast or reasoning
        description (str):
        name (str):
        prompt (str):
        editable (bool | Unset):  Default: True.
    """

    agent: str
    description: str
    name: str
    prompt: str
    editable: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        agent = self.agent

        description = self.description

        name = self.name

        prompt = self.prompt

        editable = self.editable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "agent": agent,
                "description": description,
                "name": name,
                "prompt": prompt,
            }
        )
        if editable is not UNSET:
            field_dict["editable"] = editable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        agent = d.pop("agent")

        description = d.pop("description")

        name = d.pop("name")

        prompt = d.pop("prompt")

        editable = d.pop("editable", UNSET)

        system_prompt = cls(
            agent=agent,
            description=description,
            name=name,
            prompt=prompt,
            editable=editable,
        )

        system_prompt.additional_properties = d
        return system_prompt

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
