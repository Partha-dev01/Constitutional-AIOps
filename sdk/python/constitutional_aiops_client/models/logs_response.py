from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.log_entry import LogEntry


T = TypeVar("T", bound="LogsResponse")


@_attrs_define
class LogsResponse:
    """Response containing log entries. ``source`` names where the logs came
    from (``loki``, the ``docker`` socket fallback, or ``none``) so the UI can
    show an honest, source-aware empty state.

        Attributes:
            logs (list[LogEntry]):
            total (int):
            query (None | str | Unset):
            source (str | Unset):  Default: 'loki'.
    """

    logs: list[LogEntry]
    total: int
    query: None | str | Unset = UNSET
    source: str | Unset = "loki"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        logs = []
        for logs_item_data in self.logs:
            logs_item = logs_item_data.to_dict()
            logs.append(logs_item)

        total = self.total

        query: None | str | Unset
        if isinstance(self.query, Unset):
            query = UNSET
        else:
            query = self.query

        source = self.source

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "logs": logs,
                "total": total,
            }
        )
        if query is not UNSET:
            field_dict["query"] = query
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.log_entry import LogEntry  # noqa: PLC0415

        d = dict(src_dict)
        logs = []
        _logs = d.pop("logs")
        for logs_item_data in _logs:
            logs_item = LogEntry.from_dict(logs_item_data)

            logs.append(logs_item)

        total = d.pop("total")

        def _parse_query(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        query = _parse_query(d.pop("query", UNSET))

        source = d.pop("source", UNSET)

        logs_response = cls(
            logs=logs,
            total=total,
            query=query,
            source=source,
        )

        logs_response.additional_properties = d
        return logs_response

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
