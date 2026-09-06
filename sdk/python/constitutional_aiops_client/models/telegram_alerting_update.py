from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.telegram_alerting_update_minseverity import (
    TelegramAlertingUpdateMinseverity,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="TelegramAlertingUpdate")


@_attrs_define
class TelegramAlertingUpdate:
    """
    Attributes:
        bot_token (None | str | Unset):
        chat_id (str | Unset):  Default: ''.
        enabled (bool | Unset):  Default: False.
        inbound_enabled (bool | Unset):  Default: False.
        min_severity (TelegramAlertingUpdateMinseverity | Unset):  Default: TelegramAlertingUpdateMinseverity.WARNING.
    """

    bot_token: None | str | Unset = UNSET
    chat_id: str | Unset = ""
    enabled: bool | Unset = False
    inbound_enabled: bool | Unset = False
    min_severity: TelegramAlertingUpdateMinseverity | Unset = (
        TelegramAlertingUpdateMinseverity.WARNING
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bot_token: None | str | Unset
        if isinstance(self.bot_token, Unset):
            bot_token = UNSET
        else:
            bot_token = self.bot_token

        chat_id = self.chat_id

        enabled = self.enabled

        inbound_enabled = self.inbound_enabled

        min_severity: str | Unset = UNSET
        if not isinstance(self.min_severity, Unset):
            min_severity = self.min_severity.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bot_token is not UNSET:
            field_dict["botToken"] = bot_token
        if chat_id is not UNSET:
            field_dict["chatId"] = chat_id
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if inbound_enabled is not UNSET:
            field_dict["inboundEnabled"] = inbound_enabled
        if min_severity is not UNSET:
            field_dict["minSeverity"] = min_severity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_bot_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        bot_token = _parse_bot_token(d.pop("botToken", UNSET))

        chat_id = d.pop("chatId", UNSET)

        enabled = d.pop("enabled", UNSET)

        inbound_enabled = d.pop("inboundEnabled", UNSET)

        _min_severity = d.pop("minSeverity", UNSET)
        min_severity: TelegramAlertingUpdateMinseverity | Unset
        if isinstance(_min_severity, Unset):
            min_severity = UNSET
        else:
            min_severity = TelegramAlertingUpdateMinseverity(_min_severity)

        telegram_alerting_update = cls(
            bot_token=bot_token,
            chat_id=chat_id,
            enabled=enabled,
            inbound_enabled=inbound_enabled,
            min_severity=min_severity,
        )

        telegram_alerting_update.additional_properties = d
        return telegram_alerting_update

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
