from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.serving_mode_status_swap_status import ServingModeStatusSwapStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="ServingModeStatus")


@_attrs_define
class ServingModeStatus:
    """Current serving mode + the state of any in-flight swap request.

    Attributes:
        mode (int):
        single_engine (bool):
        detail (None | str | Unset):
        requested_at (None | str | Unset):
        requested_mode (int | None | Unset):
        swap_status (ServingModeStatusSwapStatus | Unset):  Default: ServingModeStatusSwapStatus.IDLE.
        updated_at (None | str | Unset):
    """

    mode: int
    single_engine: bool
    detail: None | str | Unset = UNSET
    requested_at: None | str | Unset = UNSET
    requested_mode: int | None | Unset = UNSET
    swap_status: ServingModeStatusSwapStatus | Unset = ServingModeStatusSwapStatus.IDLE
    updated_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode = self.mode

        single_engine = self.single_engine

        detail: None | str | Unset
        if isinstance(self.detail, Unset):
            detail = UNSET
        else:
            detail = self.detail

        requested_at: None | str | Unset
        if isinstance(self.requested_at, Unset):
            requested_at = UNSET
        else:
            requested_at = self.requested_at

        requested_mode: int | None | Unset
        if isinstance(self.requested_mode, Unset):
            requested_mode = UNSET
        else:
            requested_mode = self.requested_mode

        swap_status: str | Unset = UNSET
        if not isinstance(self.swap_status, Unset):
            swap_status = self.swap_status.value

        updated_at: None | str | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "mode": mode,
                "single_engine": single_engine,
            }
        )
        if detail is not UNSET:
            field_dict["detail"] = detail
        if requested_at is not UNSET:
            field_dict["requested_at"] = requested_at
        if requested_mode is not UNSET:
            field_dict["requested_mode"] = requested_mode
        if swap_status is not UNSET:
            field_dict["swap_status"] = swap_status
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        mode = d.pop("mode")

        single_engine = d.pop("single_engine")

        def _parse_detail(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        detail = _parse_detail(d.pop("detail", UNSET))

        def _parse_requested_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        requested_at = _parse_requested_at(d.pop("requested_at", UNSET))

        def _parse_requested_mode(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        requested_mode = _parse_requested_mode(d.pop("requested_mode", UNSET))

        _swap_status = d.pop("swap_status", UNSET)
        swap_status: ServingModeStatusSwapStatus | Unset
        if isinstance(_swap_status, Unset):
            swap_status = UNSET
        else:
            swap_status = ServingModeStatusSwapStatus(_swap_status)

        def _parse_updated_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        serving_mode_status = cls(
            mode=mode,
            single_engine=single_engine,
            detail=detail,
            requested_at=requested_at,
            requested_mode=requested_mode,
            swap_status=swap_status,
            updated_at=updated_at,
        )

        serving_mode_status.additional_properties = d
        return serving_mode_status

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
