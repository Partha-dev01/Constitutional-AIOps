from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.analysis_response_result import AnalysisResponseResult


T = TypeVar("T", bound="AnalysisResponse")


@_attrs_define
class AnalysisResponse:
    """Response from analysis endpoint.

    Example:
        {'analysis_id': 'ana-456', 'confidence': 0.87, 'mode': 'rca', 'processing_time_ms': 1250.5, 'requires_approval':
            False, 'result': {'confidence': 0.87, 'remediation_steps': [{'action': 'Increase connection pool size', 'risk':
            'low'}], 'root_cause': 'Database connection pool exhaustion'}}

    Attributes:
        analysis_id (str):
        confidence (float):
        mode (str):
        processing_time_ms (float):
        result (AnalysisResponseResult):
        requires_approval (bool | Unset): Whether suggested actions require human approval Default: False.
    """

    analysis_id: str
    confidence: float
    mode: str
    processing_time_ms: float
    result: AnalysisResponseResult
    requires_approval: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        analysis_id = self.analysis_id

        confidence = self.confidence

        mode = self.mode

        processing_time_ms = self.processing_time_ms

        result = self.result.to_dict()

        requires_approval = self.requires_approval

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "analysis_id": analysis_id,
                "confidence": confidence,
                "mode": mode,
                "processing_time_ms": processing_time_ms,
                "result": result,
            }
        )
        if requires_approval is not UNSET:
            field_dict["requires_approval"] = requires_approval

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.analysis_response_result import (
            AnalysisResponseResult,  # noqa: PLC0415
        )

        d = dict(src_dict)
        analysis_id = d.pop("analysis_id")

        confidence = d.pop("confidence")

        mode = d.pop("mode")

        processing_time_ms = d.pop("processing_time_ms")

        result = AnalysisResponseResult.from_dict(d.pop("result"))

        requires_approval = d.pop("requires_approval", UNSET)

        analysis_response = cls(
            analysis_id=analysis_id,
            confidence=confidence,
            mode=mode,
            processing_time_ms=processing_time_ms,
            result=result,
            requires_approval=requires_approval,
        )

        analysis_response.additional_properties = d
        return analysis_response

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
