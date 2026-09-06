from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.generate_prompt_request_mode import GeneratePromptRequestMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.generate_prompt_request_services_item import (
        GeneratePromptRequestServicesItem,
    )
    from ..models.generate_prompt_request_topology import GeneratePromptRequestTopology


T = TypeVar("T", bound="GeneratePromptRequest")


@_attrs_define
class GeneratePromptRequest:
    """Onboarding wizard: draft a base prompt from services + topology.

    ``mode=template`` (default) is deterministic + offline; ``mode=llm`` refines
    it with the reasoning model, FALLING BACK to the template on any failure so
    setup never breaks. The draft is NOT persisted — the wizard Applies it via
    ``PUT /prompts/reasoning_chat``.

        Attributes:
            mode (GeneratePromptRequestMode | Unset):  Default: GeneratePromptRequestMode.TEMPLATE.
            services (list[GeneratePromptRequestServicesItem] | Unset):
            topology (GeneratePromptRequestTopology | Unset):
    """

    mode: GeneratePromptRequestMode | Unset = GeneratePromptRequestMode.TEMPLATE
    services: list[GeneratePromptRequestServicesItem] | Unset = UNSET
    topology: GeneratePromptRequestTopology | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        services: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.services, Unset):
            services = []
            for services_item_data in self.services:
                services_item = services_item_data.to_dict()
                services.append(services_item)

        topology: dict[str, Any] | Unset = UNSET
        if not isinstance(self.topology, Unset):
            topology = self.topology.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode
        if services is not UNSET:
            field_dict["services"] = services
        if topology is not UNSET:
            field_dict["topology"] = topology

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.generate_prompt_request_services_item import (
            GeneratePromptRequestServicesItem,  # noqa: PLC0415
        )
        from ..models.generate_prompt_request_topology import (
            GeneratePromptRequestTopology,  # noqa: PLC0415
        )

        d = dict(src_dict)
        _mode = d.pop("mode", UNSET)
        mode: GeneratePromptRequestMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = GeneratePromptRequestMode(_mode)

        _services = d.pop("services", UNSET)
        services: list[GeneratePromptRequestServicesItem] | Unset = UNSET
        if _services is not UNSET:
            services = []
            for services_item_data in _services:
                services_item = GeneratePromptRequestServicesItem.from_dict(
                    services_item_data
                )

                services.append(services_item)

        _topology = d.pop("topology", UNSET)
        topology: GeneratePromptRequestTopology | Unset
        if isinstance(_topology, Unset):
            topology = UNSET
        else:
            topology = GeneratePromptRequestTopology.from_dict(_topology)

        generate_prompt_request = cls(
            mode=mode,
            services=services,
            topology=topology,
        )

        generate_prompt_request.additional_properties = d
        return generate_prompt_request

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
