from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExplainResponse")


@_attrs_define
class ExplainResponse:
    """Uniform result. ``available`` is false for every non-spend outcome.

    Attributes:
        available (bool):
        explanation (None | str | Unset):
        model_generated (bool | Unset):  Default: False.
        reason (None | str | Unset):
        remaining (int | None | Unset):
        tokens_used (int | None | Unset):
    """

    available: bool
    explanation: None | str | Unset = UNSET
    model_generated: bool | Unset = False
    reason: None | str | Unset = UNSET
    remaining: int | None | Unset = UNSET
    tokens_used: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        available = self.available

        explanation: None | str | Unset
        if isinstance(self.explanation, Unset):
            explanation = UNSET
        else:
            explanation = self.explanation

        model_generated = self.model_generated

        reason: None | str | Unset
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        remaining: int | None | Unset
        if isinstance(self.remaining, Unset):
            remaining = UNSET
        else:
            remaining = self.remaining

        tokens_used: int | None | Unset
        if isinstance(self.tokens_used, Unset):
            tokens_used = UNSET
        else:
            tokens_used = self.tokens_used

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "available": available,
            }
        )
        if explanation is not UNSET:
            field_dict["explanation"] = explanation
        if model_generated is not UNSET:
            field_dict["model_generated"] = model_generated
        if reason is not UNSET:
            field_dict["reason"] = reason
        if remaining is not UNSET:
            field_dict["remaining"] = remaining
        if tokens_used is not UNSET:
            field_dict["tokens_used"] = tokens_used

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        available = d.pop("available")

        def _parse_explanation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        explanation = _parse_explanation(d.pop("explanation", UNSET))

        model_generated = d.pop("model_generated", UNSET)

        def _parse_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reason = _parse_reason(d.pop("reason", UNSET))

        def _parse_remaining(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        remaining = _parse_remaining(d.pop("remaining", UNSET))

        def _parse_tokens_used(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        tokens_used = _parse_tokens_used(d.pop("tokens_used", UNSET))

        explain_response = cls(
            available=available,
            explanation=explanation,
            model_generated=model_generated,
            reason=reason,
            remaining=remaining,
            tokens_used=tokens_used,
        )

        explain_response.additional_properties = d
        return explain_response

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
