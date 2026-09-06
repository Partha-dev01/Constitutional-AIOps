from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.constitutional_settings_model import ConstitutionalSettingsModel
    from ..models.notification_settings_model import NotificationSettingsModel
    from ..models.remediation_settings_model import RemediationSettingsModel
    from ..models.telemetry_settings_model import TelemetrySettingsModel


T = TypeVar("T", bound="AllSettings")


@_attrs_define
class AllSettings:
    """
    Attributes:
        constitutional (ConstitutionalSettingsModel | Unset):
        notifications (NotificationSettingsModel | Unset):
        remediation (RemediationSettingsModel | Unset): AI-remediation behaviour (Lane B demo/chaos feature).

            ``mode`` selects how a proposed restart-style action is handled:
              * ``diagnose`` (default) — never attach/execute anything; pure analysis.
              * ``approve``  — attach a proposed action; execute only on user approval.
              * ``auto``     — attempt gated execution when the interlocks all pass.
            ``autoToolAllowlist`` scopes auto mode per tool: only listed action tools may
            auto-execute; anything else degrades to an approve-style consent card. The
            default preserves the pre-allowlist behaviour (restarts eligible, scaling not).
            ``demoTargetUrl`` is shared with Lane A (chaos demo target endpoint).
        telemetry (TelemetrySettingsModel | Unset):
    """

    constitutional: ConstitutionalSettingsModel | Unset = UNSET
    notifications: NotificationSettingsModel | Unset = UNSET
    remediation: RemediationSettingsModel | Unset = UNSET
    telemetry: TelemetrySettingsModel | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        constitutional: dict[str, Any] | Unset = UNSET
        if not isinstance(self.constitutional, Unset):
            constitutional = self.constitutional.to_dict()

        notifications: dict[str, Any] | Unset = UNSET
        if not isinstance(self.notifications, Unset):
            notifications = self.notifications.to_dict()

        remediation: dict[str, Any] | Unset = UNSET
        if not isinstance(self.remediation, Unset):
            remediation = self.remediation.to_dict()

        telemetry: dict[str, Any] | Unset = UNSET
        if not isinstance(self.telemetry, Unset):
            telemetry = self.telemetry.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if constitutional is not UNSET:
            field_dict["constitutional"] = constitutional
        if notifications is not UNSET:
            field_dict["notifications"] = notifications
        if remediation is not UNSET:
            field_dict["remediation"] = remediation
        if telemetry is not UNSET:
            field_dict["telemetry"] = telemetry

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.constitutional_settings_model import (
            ConstitutionalSettingsModel,  # noqa: PLC0415
        )
        from ..models.notification_settings_model import (
            NotificationSettingsModel,  # noqa: PLC0415
        )
        from ..models.remediation_settings_model import (
            RemediationSettingsModel,  # noqa: PLC0415
        )
        from ..models.telemetry_settings_model import (
            TelemetrySettingsModel,  # noqa: PLC0415
        )

        d = dict(src_dict)
        _constitutional = d.pop("constitutional", UNSET)
        constitutional: ConstitutionalSettingsModel | Unset
        if isinstance(_constitutional, Unset):
            constitutional = UNSET
        else:
            constitutional = ConstitutionalSettingsModel.from_dict(_constitutional)

        _notifications = d.pop("notifications", UNSET)
        notifications: NotificationSettingsModel | Unset
        if isinstance(_notifications, Unset):
            notifications = UNSET
        else:
            notifications = NotificationSettingsModel.from_dict(_notifications)

        _remediation = d.pop("remediation", UNSET)
        remediation: RemediationSettingsModel | Unset
        if isinstance(_remediation, Unset):
            remediation = UNSET
        else:
            remediation = RemediationSettingsModel.from_dict(_remediation)

        _telemetry = d.pop("telemetry", UNSET)
        telemetry: TelemetrySettingsModel | Unset
        if isinstance(_telemetry, Unset):
            telemetry = UNSET
        else:
            telemetry = TelemetrySettingsModel.from_dict(_telemetry)

        all_settings = cls(
            constitutional=constitutional,
            notifications=notifications,
            remediation=remediation,
            telemetry=telemetry,
        )

        all_settings.additional_properties = d
        return all_settings

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
