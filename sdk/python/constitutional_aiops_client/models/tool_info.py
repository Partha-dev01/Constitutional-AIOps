from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tool_info_parameters import ToolInfoParameters


T = TypeVar("T", bound="ToolInfo")


@_attrs_define
class ToolInfo:
    """Tool information.

    Attributes:
        category (str):
        description (str):
        name (str):
        parameters (ToolInfoParameters):
        requires_approval (bool):
        risk_level (str):
        enabled (bool | Unset):  Default: True.
        gated_by (None | str | Unset):
    """

    category: str
    description: str
    name: str
    parameters: ToolInfoParameters
    requires_approval: bool
    risk_level: str
    enabled: bool | Unset = True
    gated_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        category = self.category

        description = self.description

        name = self.name

        parameters = self.parameters.to_dict()

        requires_approval = self.requires_approval

        risk_level = self.risk_level

        enabled = self.enabled

        gated_by: None | str | Unset
        if isinstance(self.gated_by, Unset):
            gated_by = UNSET
        else:
            gated_by = self.gated_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "category": category,
                "description": description,
                "name": name,
                "parameters": parameters,
                "requires_approval": requires_approval,
                "risk_level": risk_level,
            }
        )
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if gated_by is not UNSET:
            field_dict["gated_by"] = gated_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_info_parameters import ToolInfoParameters  # noqa: PLC0415

        d = dict(src_dict)
        category = d.pop("category")

        description = d.pop("description")

        name = d.pop("name")

        parameters = ToolInfoParameters.from_dict(d.pop("parameters"))

        requires_approval = d.pop("requires_approval")

        risk_level = d.pop("risk_level")

        enabled = d.pop("enabled", UNSET)

        def _parse_gated_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        gated_by = _parse_gated_by(d.pop("gated_by", UNSET))

        tool_info = cls(
            category=category,
            description=description,
            name=name,
            parameters=parameters,
            requires_approval=requires_approval,
            risk_level=risk_level,
            enabled=enabled,
            gated_by=gated_by,
        )

        tool_info.additional_properties = d
        return tool_info

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
