from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.analysis_request_data import AnalysisRequestData


T = TypeVar("T", bound="AnalysisRequest")


@_attrs_define
class AnalysisRequest:
    """Request for RCA or planning analysis.

    Example:
        {'data': {'affected_services': ['api-gateway', 'user-service'], 'start_time': '2025-12-14T09:00:00Z',
            'symptoms': ['High latency', 'Connection timeouts']}, 'enable_thinking': True, 'incident_id': 'INC-2024-042',
            'mode': 'rca'}

    Attributes:
        data (AnalysisRequestData): Analysis input data
        mode (str): Analysis mode: 'rca' or 'planning'
        enable_thinking (bool | Unset): Enable extended thinking Default: True.
        incident_id (None | str | Unset): Incident to analyze
    """

    data: AnalysisRequestData
    mode: str
    enable_thinking: bool | Unset = True
    incident_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        mode = self.mode

        enable_thinking = self.enable_thinking

        incident_id: None | str | Unset
        if isinstance(self.incident_id, Unset):
            incident_id = UNSET
        else:
            incident_id = self.incident_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "mode": mode,
            }
        )
        if enable_thinking is not UNSET:
            field_dict["enable_thinking"] = enable_thinking
        if incident_id is not UNSET:
            field_dict["incident_id"] = incident_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.analysis_request_data import AnalysisRequestData  # noqa: PLC0415

        d = dict(src_dict)
        data = AnalysisRequestData.from_dict(d.pop("data"))

        mode = d.pop("mode")

        enable_thinking = d.pop("enable_thinking", UNSET)

        def _parse_incident_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        incident_id = _parse_incident_id(d.pop("incident_id", UNSET))

        analysis_request = cls(
            data=data,
            mode=mode,
            enable_thinking=enable_thinking,
            incident_id=incident_id,
        )

        analysis_request.additional_properties = d
        return analysis_request

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
