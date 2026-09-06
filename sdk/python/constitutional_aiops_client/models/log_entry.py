from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.log_entry_labels import LogEntryLabels


T = TypeVar("T", bound="LogEntry")


@_attrs_define
class LogEntry:
    """Log entry from Loki.

    Attributes:
        level (str): Log level: INFO, WARN, ERROR, DEBUG
        message (str):
        service (str):
        timestamp (str):
        labels (LogEntryLabels | Unset):
    """

    level: str
    message: str
    service: str
    timestamp: str
    labels: LogEntryLabels | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        level = self.level

        message = self.message

        service = self.service

        timestamp = self.timestamp

        labels: dict[str, Any] | Unset = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "level": level,
                "message": message,
                "service": service,
                "timestamp": timestamp,
            }
        )
        if labels is not UNSET:
            field_dict["labels"] = labels

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.log_entry_labels import LogEntryLabels  # noqa: PLC0415

        d = dict(src_dict)
        level = d.pop("level")

        message = d.pop("message")

        service = d.pop("service")

        timestamp = d.pop("timestamp")

        _labels = d.pop("labels", UNSET)
        labels: LogEntryLabels | Unset
        if isinstance(_labels, Unset):
            labels = UNSET
        else:
            labels = LogEntryLabels.from_dict(_labels)

        log_entry = cls(
            level=level,
            message=message,
            service=service,
            timestamp=timestamp,
            labels=labels,
        )

        log_entry.additional_properties = d
        return log_entry

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
