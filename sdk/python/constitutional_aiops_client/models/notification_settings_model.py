from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.notification_settings_model_webhookminseverity import (
    NotificationSettingsModelWebhookminseverity,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="NotificationSettingsModel")


@_attrs_define
class NotificationSettingsModel:
    """
    Attributes:
        email_enabled (bool | Unset):  Default: False.
        notify_on_approval (bool | Unset):  Default: True.
        notify_on_critical (bool | Unset):  Default: True.
        notify_on_resolution (bool | Unset):  Default: False.
        slack_enabled (bool | Unset):  Default: False.
        webhook_enabled (bool | Unset):  Default: False.
        webhook_min_severity (NotificationSettingsModelWebhookminseverity | Unset):  Default:
            NotificationSettingsModelWebhookminseverity.WARNING.
        webhook_secret (str | Unset):  Default: ''.
        webhook_url (str | Unset):  Default: ''.
    """

    email_enabled: bool | Unset = False
    notify_on_approval: bool | Unset = True
    notify_on_critical: bool | Unset = True
    notify_on_resolution: bool | Unset = False
    slack_enabled: bool | Unset = False
    webhook_enabled: bool | Unset = False
    webhook_min_severity: NotificationSettingsModelWebhookminseverity | Unset = (
        NotificationSettingsModelWebhookminseverity.WARNING
    )
    webhook_secret: str | Unset = ""
    webhook_url: str | Unset = ""
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email_enabled = self.email_enabled

        notify_on_approval = self.notify_on_approval

        notify_on_critical = self.notify_on_critical

        notify_on_resolution = self.notify_on_resolution

        slack_enabled = self.slack_enabled

        webhook_enabled = self.webhook_enabled

        webhook_min_severity: str | Unset = UNSET
        if not isinstance(self.webhook_min_severity, Unset):
            webhook_min_severity = self.webhook_min_severity.value

        webhook_secret = self.webhook_secret

        webhook_url = self.webhook_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if email_enabled is not UNSET:
            field_dict["emailEnabled"] = email_enabled
        if notify_on_approval is not UNSET:
            field_dict["notifyOnApproval"] = notify_on_approval
        if notify_on_critical is not UNSET:
            field_dict["notifyOnCritical"] = notify_on_critical
        if notify_on_resolution is not UNSET:
            field_dict["notifyOnResolution"] = notify_on_resolution
        if slack_enabled is not UNSET:
            field_dict["slackEnabled"] = slack_enabled
        if webhook_enabled is not UNSET:
            field_dict["webhookEnabled"] = webhook_enabled
        if webhook_min_severity is not UNSET:
            field_dict["webhookMinSeverity"] = webhook_min_severity
        if webhook_secret is not UNSET:
            field_dict["webhookSecret"] = webhook_secret
        if webhook_url is not UNSET:
            field_dict["webhookUrl"] = webhook_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email_enabled = d.pop("emailEnabled", UNSET)

        notify_on_approval = d.pop("notifyOnApproval", UNSET)

        notify_on_critical = d.pop("notifyOnCritical", UNSET)

        notify_on_resolution = d.pop("notifyOnResolution", UNSET)

        slack_enabled = d.pop("slackEnabled", UNSET)

        webhook_enabled = d.pop("webhookEnabled", UNSET)

        _webhook_min_severity = d.pop("webhookMinSeverity", UNSET)
        webhook_min_severity: NotificationSettingsModelWebhookminseverity | Unset
        if isinstance(_webhook_min_severity, Unset):
            webhook_min_severity = UNSET
        else:
            webhook_min_severity = NotificationSettingsModelWebhookminseverity(
                _webhook_min_severity
            )

        webhook_secret = d.pop("webhookSecret", UNSET)

        webhook_url = d.pop("webhookUrl", UNSET)

        notification_settings_model = cls(
            email_enabled=email_enabled,
            notify_on_approval=notify_on_approval,
            notify_on_critical=notify_on_critical,
            notify_on_resolution=notify_on_resolution,
            slack_enabled=slack_enabled,
            webhook_enabled=webhook_enabled,
            webhook_min_severity=webhook_min_severity,
            webhook_secret=webhook_secret,
            webhook_url=webhook_url,
        )

        notification_settings_model.additional_properties = d
        return notification_settings_model

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
