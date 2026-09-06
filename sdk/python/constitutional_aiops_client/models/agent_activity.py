from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AgentActivity")


@_attrs_define
class AgentActivity:
    """Agent activity record.

    Attributes:
        id (str):
        input_ (str):
        latency_ms (float):
        model (str):
        output (str):
        status (str): Status: success or error
        timestamp (datetime.datetime):
        type_ (str): Activity type: annotation, classification, rca, chat, planning, action
    """

    id: str
    input_: str
    latency_ms: float
    model: str
    output: str
    status: str
    timestamp: datetime.datetime
    type_: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        input_ = self.input_

        latency_ms = self.latency_ms

        model = self.model

        output = self.output

        status = self.status

        timestamp = self.timestamp.isoformat()

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "input": input_,
                "latency_ms": latency_ms,
                "model": model,
                "output": output,
                "status": status,
                "timestamp": timestamp,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        input_ = d.pop("input")

        latency_ms = d.pop("latency_ms")

        model = d.pop("model")

        output = d.pop("output")

        status = d.pop("status")

        timestamp = datetime.datetime.fromisoformat(d.pop("timestamp"))

        type_ = d.pop("type")

        agent_activity = cls(
            id=id,
            input_=input_,
            latency_ms=latency_ms,
            model=model,
            output=output,
            status=status,
            timestamp=timestamp,
            type_=type_,
        )

        agent_activity.additional_properties = d
        return agent_activity

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
