from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RCAResult")


@_attrs_define
class RCAResult:
    """Root cause analysis result.

    Attributes:
        causal_chain (list[str]):
        confidence (float):
        root_cause (str):
        reasoning (None | str | Unset):
        similar_incidents (list[str] | None | Unset): IDs of similar past incidents
    """

    causal_chain: list[str]
    confidence: float
    root_cause: str
    reasoning: None | str | Unset = UNSET
    similar_incidents: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        causal_chain = self.causal_chain

        confidence = self.confidence

        root_cause = self.root_cause

        reasoning: None | str | Unset
        if isinstance(self.reasoning, Unset):
            reasoning = UNSET
        else:
            reasoning = self.reasoning

        similar_incidents: list[str] | None | Unset
        if isinstance(self.similar_incidents, Unset):
            similar_incidents = UNSET
        elif isinstance(self.similar_incidents, list):
            similar_incidents = self.similar_incidents

        else:
            similar_incidents = self.similar_incidents

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "causal_chain": causal_chain,
                "confidence": confidence,
                "root_cause": root_cause,
            }
        )
        if reasoning is not UNSET:
            field_dict["reasoning"] = reasoning
        if similar_incidents is not UNSET:
            field_dict["similar_incidents"] = similar_incidents

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        causal_chain = cast(list[str], d.pop("causal_chain"))

        confidence = d.pop("confidence")

        root_cause = d.pop("root_cause")

        def _parse_reasoning(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reasoning = _parse_reasoning(d.pop("reasoning", UNSET))

        def _parse_similar_incidents(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                similar_incidents_type_0 = cast(list[str], data)

                return similar_incidents_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        similar_incidents = _parse_similar_incidents(d.pop("similar_incidents", UNSET))

        rca_result = cls(
            causal_chain=causal_chain,
            confidence=confidence,
            root_cause=root_cause,
            reasoning=reasoning,
            similar_incidents=similar_incidents,
        )

        rca_result.additional_properties = d
        return rca_result

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
