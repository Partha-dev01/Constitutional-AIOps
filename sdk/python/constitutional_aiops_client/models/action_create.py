from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.action_type import ActionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action_create_evidence_type_0 import ActionCreateEvidenceType0
    from ..models.action_create_parameters_type_0 import ActionCreateParametersType0


T = TypeVar("T", bound="ActionCreate")


@_attrs_define
class ActionCreate:
    """Request to create/propose a new action.

    Example:
        {'action_type': 'restart_service', 'confidence': 0.88, 'description': 'Restart payment-service to clear memory
            leak', 'evidence': {'memory_usage': 0.95, 'restart_history': 'No restarts in 24h'}, 'incident_id':
            'INC-2024-042', 'parameters': {'graceful': True, 'timeout': 30}, 'target_instance': 'payment-service-abc123',
            'target_service': 'payment-service'}

    Attributes:
        action_type (ActionType): Types of remediation actions.
        confidence (float): Agent's confidence in this action
        description (str):
        target_service (str): Service to act on
        evidence (ActionCreateEvidenceType0 | None | Unset): Telemetry evidence supporting action
        incident_id (None | str | Unset): Related incident
        parameters (ActionCreateParametersType0 | None | Unset): Action-specific parameters
        plan_id (None | str | Unset): Part of remediation plan
        skip_validation (bool | Unset): Skip constitutional validation (admin only) Default: False.
        target_instance (None | str | Unset): Specific instance
    """

    action_type: ActionType
    confidence: float
    description: str
    target_service: str
    evidence: ActionCreateEvidenceType0 | None | Unset = UNSET
    incident_id: None | str | Unset = UNSET
    parameters: ActionCreateParametersType0 | None | Unset = UNSET
    plan_id: None | str | Unset = UNSET
    skip_validation: bool | Unset = False
    target_instance: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.action_create_evidence_type_0 import (
            ActionCreateEvidenceType0,  # noqa: PLC0415
        )
        from ..models.action_create_parameters_type_0 import (
            ActionCreateParametersType0,  # noqa: PLC0415
        )

        action_type = self.action_type.value

        confidence = self.confidence

        description = self.description

        target_service = self.target_service

        evidence: dict[str, Any] | None | Unset
        if isinstance(self.evidence, Unset):
            evidence = UNSET
        elif isinstance(self.evidence, ActionCreateEvidenceType0):
            evidence = self.evidence.to_dict()
        else:
            evidence = self.evidence

        incident_id: None | str | Unset
        if isinstance(self.incident_id, Unset):
            incident_id = UNSET
        else:
            incident_id = self.incident_id

        parameters: dict[str, Any] | None | Unset
        if isinstance(self.parameters, Unset):
            parameters = UNSET
        elif isinstance(self.parameters, ActionCreateParametersType0):
            parameters = self.parameters.to_dict()
        else:
            parameters = self.parameters

        plan_id: None | str | Unset
        if isinstance(self.plan_id, Unset):
            plan_id = UNSET
        else:
            plan_id = self.plan_id

        skip_validation = self.skip_validation

        target_instance: None | str | Unset
        if isinstance(self.target_instance, Unset):
            target_instance = UNSET
        else:
            target_instance = self.target_instance

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action_type": action_type,
                "confidence": confidence,
                "description": description,
                "target_service": target_service,
            }
        )
        if evidence is not UNSET:
            field_dict["evidence"] = evidence
        if incident_id is not UNSET:
            field_dict["incident_id"] = incident_id
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if plan_id is not UNSET:
            field_dict["plan_id"] = plan_id
        if skip_validation is not UNSET:
            field_dict["skip_validation"] = skip_validation
        if target_instance is not UNSET:
            field_dict["target_instance"] = target_instance

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action_create_evidence_type_0 import (
            ActionCreateEvidenceType0,  # noqa: PLC0415
        )
        from ..models.action_create_parameters_type_0 import (
            ActionCreateParametersType0,  # noqa: PLC0415
        )

        d = dict(src_dict)
        action_type = ActionType(d.pop("action_type"))

        confidence = d.pop("confidence")

        description = d.pop("description")

        target_service = d.pop("target_service")

        def _parse_evidence(data: object) -> ActionCreateEvidenceType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                evidence_type_0 = ActionCreateEvidenceType0.from_dict(data)

                return evidence_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ActionCreateEvidenceType0 | None | Unset, data)

        evidence = _parse_evidence(d.pop("evidence", UNSET))

        def _parse_incident_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        incident_id = _parse_incident_id(d.pop("incident_id", UNSET))

        def _parse_parameters(
            data: object,
        ) -> ActionCreateParametersType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                parameters_type_0 = ActionCreateParametersType0.from_dict(data)

                return parameters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ActionCreateParametersType0 | None | Unset, data)

        parameters = _parse_parameters(d.pop("parameters", UNSET))

        def _parse_plan_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        plan_id = _parse_plan_id(d.pop("plan_id", UNSET))

        skip_validation = d.pop("skip_validation", UNSET)

        def _parse_target_instance(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        target_instance = _parse_target_instance(d.pop("target_instance", UNSET))

        action_create = cls(
            action_type=action_type,
            confidence=confidence,
            description=description,
            target_service=target_service,
            evidence=evidence,
            incident_id=incident_id,
            parameters=parameters,
            plan_id=plan_id,
            skip_validation=skip_validation,
            target_instance=target_instance,
        )

        action_create.additional_properties = d
        return action_create

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
