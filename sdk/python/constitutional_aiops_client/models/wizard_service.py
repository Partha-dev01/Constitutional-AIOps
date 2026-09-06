from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WizardService")


@_attrs_define
class WizardService:
    """One service as entered in the onboarding Quick-Setup wizard.

    Attributes:
        name (str):
        depends_on (list[str] | Unset):
        port (int | None | Unset):
        role (str | Unset):  Default: ''.
        tier (int | None | Unset):
    """

    name: str
    depends_on: list[str] | Unset = UNSET
    port: int | None | Unset = UNSET
    role: str | Unset = ""
    tier: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        depends_on: list[str] | Unset = UNSET
        if not isinstance(self.depends_on, Unset):
            depends_on = self.depends_on

        port: int | None | Unset
        if isinstance(self.port, Unset):
            port = UNSET
        else:
            port = self.port

        role = self.role

        tier: int | None | Unset
        if isinstance(self.tier, Unset):
            tier = UNSET
        else:
            tier = self.tier

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if depends_on is not UNSET:
            field_dict["dependsOn"] = depends_on
        if port is not UNSET:
            field_dict["port"] = port
        if role is not UNSET:
            field_dict["role"] = role
        if tier is not UNSET:
            field_dict["tier"] = tier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        depends_on = cast(list[str], d.pop("dependsOn", UNSET))

        def _parse_port(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        port = _parse_port(d.pop("port", UNSET))

        role = d.pop("role", UNSET)

        def _parse_tier(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        tier = _parse_tier(d.pop("tier", UNSET))

        wizard_service = cls(
            name=name,
            depends_on=depends_on,
            port=port,
            role=role,
            tier=tier,
        )

        wizard_service.additional_properties = d
        return wizard_service

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
