from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.decision_response_result_type_0 import DecisionResponseResultType0
    from ..models.decision_response_verdict_type_0 import DecisionResponseVerdictType0


T = TypeVar("T", bound="DecisionResponse")


@_attrs_define
class DecisionResponse:
    """Outcome of acting on a proposed remediation action.

    Example:
        {'action_id': 'act-ab12cd34ef56', 'result': {'action': 'restart', 'service': 'nextcloud', 'status':
            'completed'}, 'status': 'executed', 'success': True, 'verdict': {'authorization_level': 'auto', 'can_proceed':
            True}}

    Attributes:
        action_id (str): The proposed action's id
        status (str): 'executed' (ran), 'refused' (gate declined), or 'rejected' (user declined)
        success (bool): True only when the action actually executed
        error_code (None | str | Unset): Gate/execution error class when not successful (e.g. approval_required)
        result (DecisionResponseResultType0 | None | Unset): Execution result payload, when the action ran
        verdict (DecisionResponseVerdictType0 | None | Unset): Serialized constitutional validation verdict, when
            available
    """

    action_id: str
    status: str
    success: bool
    error_code: None | str | Unset = UNSET
    result: DecisionResponseResultType0 | None | Unset = UNSET
    verdict: DecisionResponseVerdictType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.decision_response_result_type_0 import (
            DecisionResponseResultType0,  # noqa: PLC0415
        )
        from ..models.decision_response_verdict_type_0 import (
            DecisionResponseVerdictType0,  # noqa: PLC0415
        )

        action_id = self.action_id

        status = self.status

        success = self.success

        error_code: None | str | Unset
        if isinstance(self.error_code, Unset):
            error_code = UNSET
        else:
            error_code = self.error_code

        result: dict[str, Any] | None | Unset
        if isinstance(self.result, Unset):
            result = UNSET
        elif isinstance(self.result, DecisionResponseResultType0):
            result = self.result.to_dict()
        else:
            result = self.result

        verdict: dict[str, Any] | None | Unset
        if isinstance(self.verdict, Unset):
            verdict = UNSET
        elif isinstance(self.verdict, DecisionResponseVerdictType0):
            verdict = self.verdict.to_dict()
        else:
            verdict = self.verdict

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action_id": action_id,
                "status": status,
                "success": success,
            }
        )
        if error_code is not UNSET:
            field_dict["error_code"] = error_code
        if result is not UNSET:
            field_dict["result"] = result
        if verdict is not UNSET:
            field_dict["verdict"] = verdict

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.decision_response_result_type_0 import (
            DecisionResponseResultType0,  # noqa: PLC0415
        )
        from ..models.decision_response_verdict_type_0 import (
            DecisionResponseVerdictType0,  # noqa: PLC0415
        )

        d = dict(src_dict)
        action_id = d.pop("action_id")

        status = d.pop("status")

        success = d.pop("success")

        def _parse_error_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_code = _parse_error_code(d.pop("error_code", UNSET))

        def _parse_result(data: object) -> DecisionResponseResultType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                result_type_0 = DecisionResponseResultType0.from_dict(data)

                return result_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DecisionResponseResultType0 | None | Unset, data)

        result = _parse_result(d.pop("result", UNSET))

        def _parse_verdict(data: object) -> DecisionResponseVerdictType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                verdict_type_0 = DecisionResponseVerdictType0.from_dict(data)

                return verdict_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DecisionResponseVerdictType0 | None | Unset, data)

        verdict = _parse_verdict(d.pop("verdict", UNSET))

        decision_response = cls(
            action_id=action_id,
            status=status,
            success=success,
            error_code=error_code,
            result=result,
            verdict=verdict,
        )

        decision_response.additional_properties = d
        return decision_response

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
