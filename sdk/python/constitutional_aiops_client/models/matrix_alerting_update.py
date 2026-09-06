from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.matrix_alerting_update_minseverity import MatrixAlertingUpdateMinseverity
from ..types import UNSET, Unset

T = TypeVar("T", bound="MatrixAlertingUpdate")


@_attrs_define
class MatrixAlertingUpdate:
    """
    Attributes:
        access_token (None | str | Unset):
        enabled (bool | Unset):  Default: False.
        homeserver (str | Unset):  Default: ''.
        min_severity (MatrixAlertingUpdateMinseverity | Unset):  Default: MatrixAlertingUpdateMinseverity.WARNING.
        room_id (str | Unset):  Default: ''.
    """

    access_token: None | str | Unset = UNSET
    enabled: bool | Unset = False
    homeserver: str | Unset = ""
    min_severity: MatrixAlertingUpdateMinseverity | Unset = (
        MatrixAlertingUpdateMinseverity.WARNING
    )
    room_id: str | Unset = ""
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token: None | str | Unset
        if isinstance(self.access_token, Unset):
            access_token = UNSET
        else:
            access_token = self.access_token

        enabled = self.enabled

        homeserver = self.homeserver

        min_severity: str | Unset = UNSET
        if not isinstance(self.min_severity, Unset):
            min_severity = self.min_severity.value

        room_id = self.room_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if access_token is not UNSET:
            field_dict["accessToken"] = access_token
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if homeserver is not UNSET:
            field_dict["homeserver"] = homeserver
        if min_severity is not UNSET:
            field_dict["minSeverity"] = min_severity
        if room_id is not UNSET:
            field_dict["roomId"] = room_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_access_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        access_token = _parse_access_token(d.pop("accessToken", UNSET))

        enabled = d.pop("enabled", UNSET)

        homeserver = d.pop("homeserver", UNSET)

        _min_severity = d.pop("minSeverity", UNSET)
        min_severity: MatrixAlertingUpdateMinseverity | Unset
        if isinstance(_min_severity, Unset):
            min_severity = UNSET
        else:
            min_severity = MatrixAlertingUpdateMinseverity(_min_severity)

        room_id = d.pop("roomId", UNSET)

        matrix_alerting_update = cls(
            access_token=access_token,
            enabled=enabled,
            homeserver=homeserver,
            min_severity=min_severity,
            room_id=room_id,
        )

        matrix_alerting_update.additional_properties = d
        return matrix_alerting_update

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
