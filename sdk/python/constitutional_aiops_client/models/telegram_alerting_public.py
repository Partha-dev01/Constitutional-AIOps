from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.telegram_alerting_public_minseverity import (
    TelegramAlertingPublicMinseverity,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="TelegramAlertingPublic")


@_attrs_define
class TelegramAlertingPublic:
    """
    Attributes:
        chat_id (str | Unset):  Default: ''.
        enabled (bool | Unset):  Default: False.
        inbound_enabled (bool | Unset):  Default: False.
        min_severity (TelegramAlertingPublicMinseverity | Unset):  Default: TelegramAlertingPublicMinseverity.WARNING.
        routing_id (str | Unset):  Default: ''.
        token_set (bool | Unset):  Default: False.
        webhook_secret_set (bool | Unset):  Default: False.
    """

    chat_id: str | Unset = ""
    enabled: bool | Unset = False
    inbound_enabled: bool | Unset = False
    min_severity: TelegramAlertingPublicMinseverity | Unset = (
        TelegramAlertingPublicMinseverity.WARNING
    )
    routing_id: str | Unset = ""
    token_set: bool | Unset = False
    webhook_secret_set: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        chat_id = self.chat_id

        enabled = self.enabled

        inbound_enabled = self.inbound_enabled

        min_severity: str | Unset = UNSET
        if not isinstance(self.min_severity, Unset):
            min_severity = self.min_severity.value

        routing_id = self.routing_id

        token_set = self.token_set

        webhook_secret_set = self.webhook_secret_set

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if chat_id is not UNSET:
            field_dict["chatId"] = chat_id
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if inbound_enabled is not UNSET:
            field_dict["inboundEnabled"] = inbound_enabled
        if min_severity is not UNSET:
            field_dict["minSeverity"] = min_severity
        if routing_id is not UNSET:
            field_dict["routingId"] = routing_id
        if token_set is not UNSET:
            field_dict["tokenSet"] = token_set
        if webhook_secret_set is not UNSET:
            field_dict["webhookSecretSet"] = webhook_secret_set

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        chat_id = d.pop("chatId", UNSET)

        enabled = d.pop("enabled", UNSET)

        inbound_enabled = d.pop("inboundEnabled", UNSET)

        _min_severity = d.pop("minSeverity", UNSET)
        min_severity: TelegramAlertingPublicMinseverity | Unset
        if isinstance(_min_severity, Unset):
            min_severity = UNSET
        else:
            min_severity = TelegramAlertingPublicMinseverity(_min_severity)

        routing_id = d.pop("routingId", UNSET)

        token_set = d.pop("tokenSet", UNSET)

        webhook_secret_set = d.pop("webhookSecretSet", UNSET)

        telegram_alerting_public = cls(
            chat_id=chat_id,
            enabled=enabled,
            inbound_enabled=inbound_enabled,
            min_severity=min_severity,
            routing_id=routing_id,
            token_set=token_set,
            webhook_secret_set=webhook_secret_set,
        )

        telegram_alerting_public.additional_properties = d
        return telegram_alerting_public

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
