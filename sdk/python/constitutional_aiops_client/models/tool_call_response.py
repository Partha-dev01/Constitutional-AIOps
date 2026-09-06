from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tool_call_response_metadata import ToolCallResponseMetadata


T = TypeVar("T", bound="ToolCallResponse")


@_attrs_define
class ToolCallResponse:
    """Response from tool call.

    Attributes:
        data (Any):
        execution_time_ms (float):
        success (bool):
        error (None | str | Unset):
        error_code (None | str | Unset):
        metadata (ToolCallResponseMetadata | Unset):
    """

    data: Any
    execution_time_ms: float
    success: bool
    error: None | str | Unset = UNSET
    error_code: None | str | Unset = UNSET
    metadata: ToolCallResponseMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data

        execution_time_ms = self.execution_time_ms

        success = self.success

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        error_code: None | str | Unset
        if isinstance(self.error_code, Unset):
            error_code = UNSET
        else:
            error_code = self.error_code

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "execution_time_ms": execution_time_ms,
                "success": success,
            }
        )
        if error is not UNSET:
            field_dict["error"] = error
        if error_code is not UNSET:
            field_dict["error_code"] = error_code
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_call_response_metadata import (
            ToolCallResponseMetadata,  # noqa: PLC0415
        )

        d = dict(src_dict)
        data = d.pop("data")

        execution_time_ms = d.pop("execution_time_ms")

        success = d.pop("success")

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_error_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_code = _parse_error_code(d.pop("error_code", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: ToolCallResponseMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ToolCallResponseMetadata.from_dict(_metadata)

        tool_call_response = cls(
            data=data,
            execution_time_ms=execution_time_ms,
            success=success,
            error=error,
            error_code=error_code,
            metadata=metadata,
        )

        tool_call_response.additional_properties = d
        return tool_call_response

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
