from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GenerateEpisodesResponse")


@_attrs_define
class GenerateEpisodesResponse:
    """Response from episode generation.

    Attributes:
        episodes_created (int):
        errors (list[str]):
        message (str):
        services_processed (list[str]):
        success (bool):
    """

    episodes_created: int
    errors: list[str]
    message: str
    services_processed: list[str]
    success: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        episodes_created = self.episodes_created

        errors = self.errors

        message = self.message

        services_processed = self.services_processed

        success = self.success

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "episodes_created": episodes_created,
                "errors": errors,
                "message": message,
                "services_processed": services_processed,
                "success": success,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        episodes_created = d.pop("episodes_created")

        errors = cast(list[str], d.pop("errors"))

        message = d.pop("message")

        services_processed = cast(list[str], d.pop("services_processed"))

        success = d.pop("success")

        generate_episodes_response = cls(
            episodes_created=episodes_created,
            errors=errors,
            message=message,
            services_processed=services_processed,
            success=success,
        )

        generate_episodes_response.additional_properties = d
        return generate_episodes_response

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
