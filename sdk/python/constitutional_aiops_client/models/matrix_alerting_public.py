from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.matrix_alerting_public_minseverity import MatrixAlertingPublicMinseverity
from ..types import UNSET, Unset

T = TypeVar("T", bound="MatrixAlertingPublic")


@_attrs_define
class MatrixAlertingPublic:
    """
    Attributes:
        access_token_set (bool | Unset):  Default: False.
        enabled (bool | Unset):  Default: False.
        homeserver (str | Unset):  Default: ''.
        min_severity (MatrixAlertingPublicMinseverity | Unset):  Default: MatrixAlertingPublicMinseverity.WARNING.
        room_id (str | Unset):  Default: ''.
    """

    access_token_set: bool | Unset = False
    enabled: bool | Unset = False
    homeserver: str | Unset = ""
    min_severity: MatrixAlertingPublicMinseverity | Unset = (
        MatrixAlertingPublicMinseverity.WARNING
    )
    room_id: str | Unset = ""
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token_set = self.access_token_set

        enabled = self.enabled

        homeserver = self.homeserver

        min_severity: str | Unset = UNSET
        if not isinstance(self.min_severity, Unset):
            min_severity = self.min_severity.value

        room_id = self.room_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if access_token_set is not UNSET:
            field_dict["accessTokenSet"] = access_token_set
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
        access_token_set = d.pop("accessTokenSet", UNSET)

        enabled = d.pop("enabled", UNSET)

        homeserver = d.pop("homeserver", UNSET)

        _min_severity = d.pop("minSeverity", UNSET)
        min_severity: MatrixAlertingPublicMinseverity | Unset
        if isinstance(_min_severity, Unset):
            min_severity = UNSET
        else:
            min_severity = MatrixAlertingPublicMinseverity(_min_severity)

        room_id = d.pop("roomId", UNSET)

        matrix_alerting_public = cls(
            access_token_set=access_token_set,
            enabled=enabled,
            homeserver=homeserver,
            min_severity=min_severity,
            room_id=room_id,
        )

        matrix_alerting_public.additional_properties = d
        return matrix_alerting_public

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
