from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ConstitutionalSettingsModel")


@_attrs_define
class ConstitutionalSettingsModel:
    """
    Attributes:
        approval_threshold (int | Unset):  Default: 70.
        auto_threshold (int | Unset):  Default: 90.
        enable_audit_log (bool | Unset):  Default: True.
        enable_learning (bool | Unset):  Default: True.
        max_actions_per_minute (int | Unset):  Default: 10.
        strict_tier_1 (bool | Unset):  Default: True.
    """

    approval_threshold: int | Unset = 70
    auto_threshold: int | Unset = 90
    enable_audit_log: bool | Unset = True
    enable_learning: bool | Unset = True
    max_actions_per_minute: int | Unset = 10
    strict_tier_1: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        approval_threshold = self.approval_threshold

        auto_threshold = self.auto_threshold

        enable_audit_log = self.enable_audit_log

        enable_learning = self.enable_learning

        max_actions_per_minute = self.max_actions_per_minute

        strict_tier_1 = self.strict_tier_1

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if approval_threshold is not UNSET:
            field_dict["approvalThreshold"] = approval_threshold
        if auto_threshold is not UNSET:
            field_dict["autoThreshold"] = auto_threshold
        if enable_audit_log is not UNSET:
            field_dict["enableAuditLog"] = enable_audit_log
        if enable_learning is not UNSET:
            field_dict["enableLearning"] = enable_learning
        if max_actions_per_minute is not UNSET:
            field_dict["maxActionsPerMinute"] = max_actions_per_minute
        if strict_tier_1 is not UNSET:
            field_dict["strictTier1"] = strict_tier_1

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        approval_threshold = d.pop("approvalThreshold", UNSET)

        auto_threshold = d.pop("autoThreshold", UNSET)

        enable_audit_log = d.pop("enableAuditLog", UNSET)

        enable_learning = d.pop("enableLearning", UNSET)

        max_actions_per_minute = d.pop("maxActionsPerMinute", UNSET)

        strict_tier_1 = d.pop("strictTier1", UNSET)

        constitutional_settings_model = cls(
            approval_threshold=approval_threshold,
            auto_threshold=auto_threshold,
            enable_audit_log=enable_audit_log,
            enable_learning=enable_learning,
            max_actions_per_minute=max_actions_per_minute,
            strict_tier_1=strict_tier_1,
        )

        constitutional_settings_model.additional_properties = d
        return constitutional_settings_model

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
