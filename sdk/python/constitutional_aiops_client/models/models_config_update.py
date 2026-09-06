from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ModelsConfigUpdate")


@_attrs_define
class ModelsConfigUpdate:
    """Editable LLM-endpoint config (PUT).

    Attributes:
        fast_agent_model (str):
        fast_agent_url (str):
        reasoning_agent_model (str):
        reasoning_agent_url (str):
        api_key (None | str | Unset):
    """

    fast_agent_model: str
    fast_agent_url: str
    reasoning_agent_model: str
    reasoning_agent_url: str
    api_key: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fast_agent_model = self.fast_agent_model

        fast_agent_url = self.fast_agent_url

        reasoning_agent_model = self.reasoning_agent_model

        reasoning_agent_url = self.reasoning_agent_url

        api_key: None | str | Unset
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

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
        if api_key is not UNSET:
            field_dict["apiKey"] = api_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        fast_agent_model = d.pop("fastAgentModel")

        fast_agent_url = d.pop("fastAgentUrl")

        reasoning_agent_model = d.pop("reasoningAgentModel")

        reasoning_agent_url = d.pop("reasoningAgentUrl")

        def _parse_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_key = _parse_api_key(d.pop("apiKey", UNSET))

        models_config_update = cls(
            fast_agent_model=fast_agent_model,
            fast_agent_url=fast_agent_url,
            reasoning_agent_model=reasoning_agent_model,
            reasoning_agent_url=reasoning_agent_url,
            api_key=api_key,
        )

        models_config_update.additional_properties = d
        return models_config_update

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
