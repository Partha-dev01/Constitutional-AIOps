from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.explain_request_payload import ExplainRequestPayload


T = TypeVar("T", bound="ExplainRequest")


@_attrs_define
class ExplainRequest:
    """A request for a plain-language explanation of a widget's computed data.

    Attributes:
        kind (str | Unset):  Default: 'generic'.
        payload (ExplainRequestPayload | Unset):
        tier (str | Unset):  Default: 'fast'.
    """

    kind: str | Unset = "generic"
    payload: ExplainRequestPayload | Unset = UNSET
    tier: str | Unset = "fast"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kind = self.kind

        payload: dict[str, Any] | Unset = UNSET
        if not isinstance(self.payload, Unset):
            payload = self.payload.to_dict()

        tier = self.tier

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kind is not UNSET:
            field_dict["kind"] = kind
        if payload is not UNSET:
            field_dict["payload"] = payload
        if tier is not UNSET:
            field_dict["tier"] = tier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.explain_request_payload import ExplainRequestPayload  # noqa: PLC0415

        d = dict(src_dict)
        kind = d.pop("kind", UNSET)

        _payload = d.pop("payload", UNSET)
        payload: ExplainRequestPayload | Unset
        if isinstance(_payload, Unset):
            payload = UNSET
        else:
            payload = ExplainRequestPayload.from_dict(_payload)

        tier = d.pop("tier", UNSET)

        explain_request = cls(
            kind=kind,
            payload=payload,
            tier=tier,
        )

        explain_request.additional_properties = d
        return explain_request

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
