from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.authorization_level import AuthorizationLevel
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.constitutional_validation_violations_item import (
        ConstitutionalValidationViolationsItem,
    )


T = TypeVar("T", bound="ConstitutionalValidation")


@_attrs_define
class ConstitutionalValidation:
    """Result of constitutional validation.

    Example:
        {'authorization_level': 'automatic', 'confidence': 0.92, 'explanation': 'Validation passed - automatic
            authorization', 'passed': True, 'tier1_passed': True, 'tier2_passed': True, 'tier3_passed': True,
            'validated_at': '2025-12-14T10:30:00Z', 'violations': [], 'warnings': []}

    Attributes:
        authorization_level (AuthorizationLevel): Authorization levels from Constitutional AI.
        confidence (float):
        explanation (str): Human-readable explanation
        passed (bool):
        tier1_passed (bool): Safety principles passed
        tier2_passed (bool): Operational principles passed
        tier3_passed (bool): Learning principles passed
        validated_at (datetime.datetime):
        violations (list[ConstitutionalValidationViolationsItem] | Unset): List of principle violations
        warnings (list[str] | Unset): Non-blocking warnings
    """

    authorization_level: AuthorizationLevel
    confidence: float
    explanation: str
    passed: bool
    tier1_passed: bool
    tier2_passed: bool
    tier3_passed: bool
    validated_at: datetime.datetime
    violations: list[ConstitutionalValidationViolationsItem] | Unset = UNSET
    warnings: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        authorization_level = self.authorization_level.value

        confidence = self.confidence

        explanation = self.explanation

        passed = self.passed

        tier1_passed = self.tier1_passed

        tier2_passed = self.tier2_passed

        tier3_passed = self.tier3_passed

        validated_at = self.validated_at.isoformat()

        violations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.violations, Unset):
            violations = []
            for violations_item_data in self.violations:
                violations_item = violations_item_data.to_dict()
                violations.append(violations_item)

        warnings: list[str] | Unset = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = self.warnings

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "authorization_level": authorization_level,
                "confidence": confidence,
                "explanation": explanation,
                "passed": passed,
                "tier1_passed": tier1_passed,
                "tier2_passed": tier2_passed,
                "tier3_passed": tier3_passed,
                "validated_at": validated_at,
            }
        )
        if violations is not UNSET:
            field_dict["violations"] = violations
        if warnings is not UNSET:
            field_dict["warnings"] = warnings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.constitutional_validation_violations_item import (
            ConstitutionalValidationViolationsItem,  # noqa: PLC0415
        )

        d = dict(src_dict)
        authorization_level = AuthorizationLevel(d.pop("authorization_level"))

        confidence = d.pop("confidence")

        explanation = d.pop("explanation")

        passed = d.pop("passed")

        tier1_passed = d.pop("tier1_passed")

        tier2_passed = d.pop("tier2_passed")

        tier3_passed = d.pop("tier3_passed")

        validated_at = datetime.datetime.fromisoformat(d.pop("validated_at"))

        _violations = d.pop("violations", UNSET)
        violations: list[ConstitutionalValidationViolationsItem] | Unset = UNSET
        if _violations is not UNSET:
            violations = []
            for violations_item_data in _violations:
                violations_item = ConstitutionalValidationViolationsItem.from_dict(
                    violations_item_data
                )

                violations.append(violations_item)

        warnings = cast(list[str], d.pop("warnings", UNSET))

        constitutional_validation = cls(
            authorization_level=authorization_level,
            confidence=confidence,
            explanation=explanation,
            passed=passed,
            tier1_passed=tier1_passed,
            tier2_passed=tier2_passed,
            tier3_passed=tier3_passed,
            validated_at=validated_at,
            violations=violations,
            warnings=warnings,
        )

        constitutional_validation.additional_properties = d
        return constitutional_validation

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
