from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DismissHostResponse")


@_attrs_define
class DismissHostResponse:
    """Result of dismissing/restoring a monitored remote host.

    Attributes:
        dismissed (bool):
        edge_label (str):
        message (str):
    """

    dismissed: bool
    edge_label: str
    message: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dismissed = self.dismissed

        edge_label = self.edge_label

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dismissed": dismissed,
                "edge_label": edge_label,
                "message": message,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dismissed = d.pop("dismissed")

        edge_label = d.pop("edge_label")

        message = d.pop("message")

        dismiss_host_response = cls(
            dismissed=dismissed,
            edge_label=edge_label,
            message=message,
        )

        dismiss_host_response.additional_properties = d
        return dismiss_host_response

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
