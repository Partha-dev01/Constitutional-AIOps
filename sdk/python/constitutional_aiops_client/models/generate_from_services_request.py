from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.generate_from_services_request_mode import GenerateFromServicesRequestMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.wizard_service import WizardService


T = TypeVar("T", bound="GenerateFromServicesRequest")


@_attrs_define
class GenerateFromServicesRequest:
    """Structured services list from the wizard's Services step.

    ``mode`` picks how the candidate is built:
      * ``template`` (default) — deterministic, offline, no LLM.
      * ``llm`` — refine the template with the reasoning model, FALLING BACK to
        the template on any failure so setup never breaks.

        Attributes:
            mode (GenerateFromServicesRequestMode | Unset):  Default: GenerateFromServicesRequestMode.TEMPLATE.
            services (list[WizardService] | Unset):
    """

    mode: GenerateFromServicesRequestMode | Unset = (
        GenerateFromServicesRequestMode.TEMPLATE
    )
    services: list[WizardService] | Unset = UNSET
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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode
        if services is not UNSET:
            field_dict["services"] = services

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.wizard_service import WizardService  # noqa: PLC0415

        d = dict(src_dict)
        _mode = d.pop("mode", UNSET)
        mode: GenerateFromServicesRequestMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = GenerateFromServicesRequestMode(_mode)

        _services = d.pop("services", UNSET)
        services: list[WizardService] | Unset = UNSET
        if _services is not UNSET:
            services = []
            for services_item_data in _services:
                services_item = WizardService.from_dict(services_item_data)

                services.append(services_item)

        generate_from_services_request = cls(
            mode=mode,
            services=services,
        )

        generate_from_services_request.additional_properties = d
        return generate_from_services_request

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
