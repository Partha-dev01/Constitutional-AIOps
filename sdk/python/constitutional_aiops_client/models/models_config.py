from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ModelsConfig")


@_attrs_define
class ModelsConfig:
    """Effective LLM-endpoint config (GET). Never carries the API key itself.

    Attributes:
        fast_agent_model (str):
        fast_agent_url (str):
        reasoning_agent_model (str):
        reasoning_agent_url (str):
        fast_api_key_set (bool | Unset):  Default: False.
        reasoning_api_key_set (bool | Unset):  Default: False.
    """

    fast_agent_model: str
    fast_agent_url: str
    reasoning_agent_model: str
    reasoning_agent_url: str
    fast_api_key_set: bool | Unset = False
    reasoning_api_key_set: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fast_agent_model = self.fast_agent_model

        fast_agent_url = self.fast_agent_url

        reasoning_agent_model = self.reasoning_agent_model

        reasoning_agent_url = self.reasoning_agent_url

        fast_api_key_set = self.fast_api_key_set

        reasoning_api_key_set = self.reasoning_api_key_set

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "fastAgentModel": fast_agent_model,
                "fastAgentUrl": fast_agent_url,
                "reasoningAgentModel": reasoning_agent_model,
                "reasoningAgentUrl": reasoning_agent_url,
            }
        )
        if fast_api_key_set is not UNSET:
            field_dict["fastApiKeySet"] = fast_api_key_set
        if reasoning_api_key_set is not UNSET:
            field_dict["reasoningApiKeySet"] = reasoning_api_key_set

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        fast_agent_model = d.pop("fastAgentModel")

        fast_agent_url = d.pop("fastAgentUrl")

        reasoning_agent_model = d.pop("reasoningAgentModel")

        reasoning_agent_url = d.pop("reasoningAgentUrl")

        fast_api_key_set = d.pop("fastApiKeySet", UNSET)

        reasoning_api_key_set = d.pop("reasoningApiKeySet", UNSET)

        models_config = cls(
            fast_agent_model=fast_agent_model,
            fast_agent_url=fast_agent_url,
            reasoning_agent_model=reasoning_agent_model,
            reasoning_agent_url=reasoning_agent_url,
            fast_api_key_set=fast_api_key_set,
            reasoning_api_key_set=reasoning_api_key_set,
        )

        models_config.additional_properties = d
        return models_config

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
