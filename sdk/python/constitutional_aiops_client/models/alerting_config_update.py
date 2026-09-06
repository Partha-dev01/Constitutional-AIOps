from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.matrix_alerting_update import MatrixAlertingUpdate
    from ..models.telegram_alerting_update import TelegramAlertingUpdate


T = TypeVar("T", bound="AlertingConfigUpdate")


@_attrs_define
class AlertingConfigUpdate:
    """
    Attributes:
        matrix (MatrixAlertingUpdate | Unset):
        telegram (TelegramAlertingUpdate | Unset):
    """

    matrix: MatrixAlertingUpdate | Unset = UNSET
    telegram: TelegramAlertingUpdate | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        matrix: dict[str, Any] | Unset = UNSET
        if not isinstance(self.matrix, Unset):
            matrix = self.matrix.to_dict()

        telegram: dict[str, Any] | Unset = UNSET
        if not isinstance(self.telegram, Unset):
            telegram = self.telegram.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if matrix is not UNSET:
            field_dict["matrix"] = matrix
        if telegram is not UNSET:
            field_dict["telegram"] = telegram

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.matrix_alerting_update import (
            MatrixAlertingUpdate,  # noqa: PLC0415
        )
        from ..models.telegram_alerting_update import (
            TelegramAlertingUpdate,  # noqa: PLC0415
        )

        d = dict(src_dict)
        _matrix = d.pop("matrix", UNSET)
        matrix: MatrixAlertingUpdate | Unset
        if isinstance(_matrix, Unset):
            matrix = UNSET
        else:
            matrix = MatrixAlertingUpdate.from_dict(_matrix)

        _telegram = d.pop("telegram", UNSET)
        telegram: TelegramAlertingUpdate | Unset
        if isinstance(_telegram, Unset):
            telegram = UNSET
        else:
            telegram = TelegramAlertingUpdate.from_dict(_telegram)

        alerting_config_update = cls(
            matrix=matrix,
            telegram=telegram,
        )

        alerting_config_update.additional_properties = d
        return alerting_config_update

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
