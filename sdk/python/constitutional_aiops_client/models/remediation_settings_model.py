from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.remediation_settings_model_auto_tool_allowlist_item import (
    RemediationSettingsModelAutoToolAllowlistItem,
)
from ..models.remediation_settings_model_mode import RemediationSettingsModelMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="RemediationSettingsModel")


@_attrs_define
class RemediationSettingsModel:
    """AI-remediation behaviour (Lane B demo/chaos feature).

    ``mode`` selects how a proposed restart-style action is handled:
      * ``diagnose`` (default) — never attach/execute anything; pure analysis.
      * ``approve``  — attach a proposed action; execute only on user approval.
      * ``auto``     — attempt gated execution when the interlocks all pass.
    ``autoToolAllowlist`` scopes auto mode per tool: only listed action tools may
    auto-execute; anything else degrades to an approve-style consent card. The
    default preserves the pre-allowlist behaviour (restarts eligible, scaling not).
    ``demoTargetUrl`` is shared with Lane A (chaos demo target endpoint).

        Attributes:
            auto_confidence_threshold (int | Unset):  Default: 90.
            auto_tool_allowlist (list[RemediationSettingsModelAutoToolAllowlistItem] | Unset):
            demo_target_url (str | Unset):  Default: ''.
            mode (RemediationSettingsModelMode | Unset):  Default: RemediationSettingsModelMode.DIAGNOSE.
            require_evidence_for_auto (bool | Unset):  Default: True.
    """

    auto_confidence_threshold: int | Unset = 90
    auto_tool_allowlist: list[RemediationSettingsModelAutoToolAllowlistItem] | Unset = (
        UNSET
    )
    demo_target_url: str | Unset = ""
    mode: RemediationSettingsModelMode | Unset = RemediationSettingsModelMode.DIAGNOSE
    require_evidence_for_auto: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_confidence_threshold = self.auto_confidence_threshold

        auto_tool_allowlist: list[str] | Unset = UNSET
        if not isinstance(self.auto_tool_allowlist, Unset):
            auto_tool_allowlist = []
            for auto_tool_allowlist_item_data in self.auto_tool_allowlist:
                auto_tool_allowlist_item = auto_tool_allowlist_item_data.value
                auto_tool_allowlist.append(auto_tool_allowlist_item)

        demo_target_url = self.demo_target_url

        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        require_evidence_for_auto = self.require_evidence_for_auto

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if auto_confidence_threshold is not UNSET:
            field_dict["autoConfidenceThreshold"] = auto_confidence_threshold
        if auto_tool_allowlist is not UNSET:
            field_dict["autoToolAllowlist"] = auto_tool_allowlist
        if demo_target_url is not UNSET:
            field_dict["demoTargetUrl"] = demo_target_url
        if mode is not UNSET:
            field_dict["mode"] = mode
        if require_evidence_for_auto is not UNSET:
            field_dict["requireEvidenceForAuto"] = require_evidence_for_auto

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        auto_confidence_threshold = d.pop("autoConfidenceThreshold", UNSET)

        _auto_tool_allowlist = d.pop("autoToolAllowlist", UNSET)
        auto_tool_allowlist: (
            list[RemediationSettingsModelAutoToolAllowlistItem] | Unset
        ) = UNSET
        if _auto_tool_allowlist is not UNSET:
            auto_tool_allowlist = []
            for auto_tool_allowlist_item_data in _auto_tool_allowlist:
                auto_tool_allowlist_item = (
                    RemediationSettingsModelAutoToolAllowlistItem(
                        auto_tool_allowlist_item_data
                    )
                )

                auto_tool_allowlist.append(auto_tool_allowlist_item)

        demo_target_url = d.pop("demoTargetUrl", UNSET)

        _mode = d.pop("mode", UNSET)
        mode: RemediationSettingsModelMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = RemediationSettingsModelMode(_mode)

        require_evidence_for_auto = d.pop("requireEvidenceForAuto", UNSET)

        remediation_settings_model = cls(
            auto_confidence_threshold=auto_confidence_threshold,
            auto_tool_allowlist=auto_tool_allowlist,
            demo_target_url=demo_target_url,
            mode=mode,
            require_evidence_for_auto=require_evidence_for_auto,
        )

        remediation_settings_model.additional_properties = d
        return remediation_settings_model

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
