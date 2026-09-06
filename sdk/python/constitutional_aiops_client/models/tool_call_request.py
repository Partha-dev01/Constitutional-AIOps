from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tool_call_request_context_type_0 import ToolCallRequestContextType0
    from ..models.tool_call_request_parameters import ToolCallRequestParameters


T = TypeVar("T", bound="ToolCallRequest")


@_attrs_define
class ToolCallRequest:
    """Request to call a tool.

    Attributes:
        tool_name (str): Name of the tool to call
        context (None | ToolCallRequestContextType0 | Unset): Additional context
        parameters (ToolCallRequestParameters | Unset): Tool parameters
    """

    tool_name: str
    context: None | ToolCallRequestContextType0 | Unset = UNSET
    parameters: ToolCallRequestParameters | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.tool_call_request_context_type_0 import (
            ToolCallRequestContextType0,  # noqa: PLC0415
        )

        tool_name = self.tool_name

        context: dict[str, Any] | None | Unset
        if isinstance(self.context, Unset):
            context = UNSET
        elif isinstance(self.context, ToolCallRequestContextType0):
            context = self.context.to_dict()
        else:
            context = self.context

        parameters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tool_name": tool_name,
            }
        )
        if context is not UNSET:
            field_dict["context"] = context
        if parameters is not UNSET:
            field_dict["parameters"] = parameters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_call_request_context_type_0 import (
            ToolCallRequestContextType0,  # noqa: PLC0415
        )
        from ..models.tool_call_request_parameters import (
            ToolCallRequestParameters,  # noqa: PLC0415
        )

        d = dict(src_dict)
        tool_name = d.pop("tool_name")

        def _parse_context(data: object) -> None | ToolCallRequestContextType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                context_type_0 = ToolCallRequestContextType0.from_dict(data)

                return context_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ToolCallRequestContextType0 | Unset, data)

        context = _parse_context(d.pop("context", UNSET))

        _parameters = d.pop("parameters", UNSET)
        parameters: ToolCallRequestParameters | Unset
        if isinstance(_parameters, Unset):
            parameters = UNSET
        else:
            parameters = ToolCallRequestParameters.from_dict(_parameters)

        tool_call_request = cls(
            tool_name=tool_name,
            context=context,
            parameters=parameters,
        )

        tool_call_request.additional_properties = d
        return tool_call_request

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
