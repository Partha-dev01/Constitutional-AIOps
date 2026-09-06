from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.action_status import ActionStatus
from ..models.action_type import ActionType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action_audit_log_item import ActionAuditLogItem
    from ..models.action_execution_result import ActionExecutionResult
    from ..models.action_parameters_type_0 import ActionParametersType0
    from ..models.constitutional_validation import ConstitutionalValidation


T = TypeVar("T", bound="Action")


@_attrs_define
class Action:
    """Complete action record.

    Example:
        {'action_type': 'restart_service', 'confidence': 0.88, 'created_at': '2025-12-14T10:30:00Z', 'created_by':
            'system', 'description': 'Restart payment-service to clear memory leak', 'id': 'ACT-2024-001234', 'incident_id':
            'INC-2024-042', 'requires_approval': False, 'status': 'completed', 'target_service': 'payment-service',
            'updated_at': '2025-12-14T10:32:45Z'}

    Attributes:
        action_type (ActionType): Types of remediation actions.
        confidence (float):
        created_at (datetime.datetime):
        description (str):
        id (str): Unique action ID
        target_service (str): Service to act on
        updated_at (datetime.datetime):
        approval_comments (None | str | Unset):
        approved_at (datetime.datetime | None | Unset):
        approved_by (None | str | Unset):
        audit_log (list[ActionAuditLogItem] | Unset): Action lifecycle audit trail
        created_by (str | Unset): Creator (system or user ID) Default: 'system'.
        execution_result (ActionExecutionResult | None | Unset):
        expires_at (datetime.datetime | None | Unset): Approval expiration time
        incident_id (None | str | Unset):
        parameters (ActionParametersType0 | None | Unset): Action-specific parameters
        plan_id (None | str | Unset):
        requires_approval (bool | Unset):  Default: False.
        status (ActionStatus | Unset): Action execution status.
        target_instance (None | str | Unset): Specific instance
        validation (ConstitutionalValidation | None | Unset):
    """

    action_type: ActionType
    confidence: float
    created_at: datetime.datetime
    description: str
    id: str
    target_service: str
    updated_at: datetime.datetime
    approval_comments: None | str | Unset = UNSET
    approved_at: datetime.datetime | None | Unset = UNSET
    approved_by: None | str | Unset = UNSET
    audit_log: list[ActionAuditLogItem] | Unset = UNSET
    created_by: str | Unset = "system"
    execution_result: ActionExecutionResult | None | Unset = UNSET
    expires_at: datetime.datetime | None | Unset = UNSET
    incident_id: None | str | Unset = UNSET
    parameters: ActionParametersType0 | None | Unset = UNSET
    plan_id: None | str | Unset = UNSET
    requires_approval: bool | Unset = False
    status: ActionStatus | Unset = UNSET
    target_instance: None | str | Unset = UNSET
    validation: ConstitutionalValidation | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.action_execution_result import (
            ActionExecutionResult,  # noqa: PLC0415
        )
        from ..models.action_parameters_type_0 import (
            ActionParametersType0,  # noqa: PLC0415
        )
        from ..models.constitutional_validation import (
            ConstitutionalValidation,  # noqa: PLC0415
        )

        action_type = self.action_type.value

        confidence = self.confidence

        created_at = self.created_at.isoformat()

        description = self.description

        id = self.id

        target_service = self.target_service

        updated_at = self.updated_at.isoformat()

        approval_comments: None | str | Unset
        if isinstance(self.approval_comments, Unset):
            approval_comments = UNSET
        else:
            approval_comments = self.approval_comments

        approved_at: None | str | Unset
        if isinstance(self.approved_at, Unset):
            approved_at = UNSET
        elif isinstance(self.approved_at, datetime.datetime):
            approved_at = self.approved_at.isoformat()
        else:
            approved_at = self.approved_at

        approved_by: None | str | Unset
        if isinstance(self.approved_by, Unset):
            approved_by = UNSET
        else:
            approved_by = self.approved_by

        audit_log: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.audit_log, Unset):
            audit_log = []
            for audit_log_item_data in self.audit_log:
                audit_log_item = audit_log_item_data.to_dict()
                audit_log.append(audit_log_item)

        created_by = self.created_by

        execution_result: dict[str, Any] | None | Unset
        if isinstance(self.execution_result, Unset):
            execution_result = UNSET
        elif isinstance(self.execution_result, ActionExecutionResult):
            execution_result = self.execution_result.to_dict()
        else:
            execution_result = self.execution_result

        expires_at: None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        elif isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        incident_id: None | str | Unset
        if isinstance(self.incident_id, Unset):
            incident_id = UNSET
        else:
            incident_id = self.incident_id

        parameters: dict[str, Any] | None | Unset
        if isinstance(self.parameters, Unset):
            parameters = UNSET
        elif isinstance(self.parameters, ActionParametersType0):
            parameters = self.parameters.to_dict()
        else:
            parameters = self.parameters

        plan_id: None | str | Unset
        if isinstance(self.plan_id, Unset):
            plan_id = UNSET
        else:
            plan_id = self.plan_id

        requires_approval = self.requires_approval

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        target_instance: None | str | Unset
        if isinstance(self.target_instance, Unset):
            target_instance = UNSET
        else:
            target_instance = self.target_instance

        validation: dict[str, Any] | None | Unset
        if isinstance(self.validation, Unset):
            validation = UNSET
        elif isinstance(self.validation, ConstitutionalValidation):
            validation = self.validation.to_dict()
        else:
            validation = self.validation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action_type": action_type,
                "confidence": confidence,
                "created_at": created_at,
                "description": description,
                "id": id,
                "target_service": target_service,
                "updated_at": updated_at,
            }
        )
        if approval_comments is not UNSET:
            field_dict["approval_comments"] = approval_comments
        if approved_at is not UNSET:
            field_dict["approved_at"] = approved_at
        if approved_by is not UNSET:
            field_dict["approved_by"] = approved_by
        if audit_log is not UNSET:
            field_dict["audit_log"] = audit_log
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if execution_result is not UNSET:
            field_dict["execution_result"] = execution_result
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if incident_id is not UNSET:
            field_dict["incident_id"] = incident_id
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if plan_id is not UNSET:
            field_dict["plan_id"] = plan_id
        if requires_approval is not UNSET:
            field_dict["requires_approval"] = requires_approval
        if status is not UNSET:
            field_dict["status"] = status
        if target_instance is not UNSET:
            field_dict["target_instance"] = target_instance
        if validation is not UNSET:
            field_dict["validation"] = validation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action_audit_log_item import ActionAuditLogItem  # noqa: PLC0415
        from ..models.action_execution_result import (
            ActionExecutionResult,  # noqa: PLC0415
        )
        from ..models.action_parameters_type_0 import (
            ActionParametersType0,  # noqa: PLC0415
        )
        from ..models.constitutional_validation import (
            ConstitutionalValidation,  # noqa: PLC0415
        )

        d = dict(src_dict)
        action_type = ActionType(d.pop("action_type"))

        confidence = d.pop("confidence")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        description = d.pop("description")

        id = d.pop("id")

        target_service = d.pop("target_service")

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_approval_comments(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        approval_comments = _parse_approval_comments(d.pop("approval_comments", UNSET))

        def _parse_approved_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                approved_at_type_0 = datetime.datetime.fromisoformat(data)

                return approved_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        approved_at = _parse_approved_at(d.pop("approved_at", UNSET))

        def _parse_approved_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        approved_by = _parse_approved_by(d.pop("approved_by", UNSET))

        _audit_log = d.pop("audit_log", UNSET)
        audit_log: list[ActionAuditLogItem] | Unset = UNSET
        if _audit_log is not UNSET:
            audit_log = []
            for audit_log_item_data in _audit_log:
                audit_log_item = ActionAuditLogItem.from_dict(audit_log_item_data)

                audit_log.append(audit_log_item)

        created_by = d.pop("created_by", UNSET)

        def _parse_execution_result(
            data: object,
        ) -> ActionExecutionResult | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                execution_result_type_0 = ActionExecutionResult.from_dict(data)

                return execution_result_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ActionExecutionResult | None | Unset, data)

        execution_result = _parse_execution_result(d.pop("execution_result", UNSET))

        def _parse_expires_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = datetime.datetime.fromisoformat(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        expires_at = _parse_expires_at(d.pop("expires_at", UNSET))

        def _parse_incident_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        incident_id = _parse_incident_id(d.pop("incident_id", UNSET))

        def _parse_parameters(data: object) -> ActionParametersType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                parameters_type_0 = ActionParametersType0.from_dict(data)

                return parameters_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ActionParametersType0 | None | Unset, data)

        parameters = _parse_parameters(d.pop("parameters", UNSET))

        def _parse_plan_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        plan_id = _parse_plan_id(d.pop("plan_id", UNSET))

        requires_approval = d.pop("requires_approval", UNSET)

        _status = d.pop("status", UNSET)
        status: ActionStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ActionStatus(_status)

        def _parse_target_instance(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        target_instance = _parse_target_instance(d.pop("target_instance", UNSET))

        def _parse_validation(data: object) -> ConstitutionalValidation | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                validation_type_0 = ConstitutionalValidation.from_dict(data)

                return validation_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ConstitutionalValidation | None | Unset, data)

        validation = _parse_validation(d.pop("validation", UNSET))

        action = cls(
            action_type=action_type,
            confidence=confidence,
            created_at=created_at,
            description=description,
            id=id,
            target_service=target_service,
            updated_at=updated_at,
            approval_comments=approval_comments,
            approved_at=approved_at,
            approved_by=approved_by,
            audit_log=audit_log,
            created_by=created_by,
            execution_result=execution_result,
            expires_at=expires_at,
            incident_id=incident_id,
            parameters=parameters,
            plan_id=plan_id,
            requires_approval=requires_approval,
            status=status,
            target_instance=target_instance,
            validation=validation,
        )

        action.additional_properties = d
        return action

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
