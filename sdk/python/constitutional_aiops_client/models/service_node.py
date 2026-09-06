from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.service_node_metadata import ServiceNodeMetadata


T = TypeVar("T", bound="ServiceNode")


@_attrs_define
class ServiceNode:
    """Service node - only shown when affected by episodes.

    Attributes:
        name (str):
        incident_count (int | Unset): Number of incidents affecting this service Default: 0.
        last_incident (datetime.datetime | None | Unset): Last incident timestamp
        metadata (ServiceNodeMetadata | Unset):
        status (str | Unset): Status: healthy, warning, critical Default: 'healthy'.
        type_ (str | Unset):  Default: 'service'.
    """

    name: str
    incident_count: int | Unset = 0
    last_incident: datetime.datetime | None | Unset = UNSET
    metadata: ServiceNodeMetadata | Unset = UNSET
    status: str | Unset = "healthy"
    type_: str | Unset = "service"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        incident_count = self.incident_count

        last_incident: None | str | Unset
        if isinstance(self.last_incident, Unset):
            last_incident = UNSET
        elif isinstance(self.last_incident, datetime.datetime):
            last_incident = self.last_incident.isoformat()
        else:
            last_incident = self.last_incident

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        status = self.status

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if incident_count is not UNSET:
            field_dict["incident_count"] = incident_count
        if last_incident is not UNSET:
            field_dict["last_incident"] = last_incident
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if status is not UNSET:
            field_dict["status"] = status
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.service_node_metadata import ServiceNodeMetadata  # noqa: PLC0415

        d = dict(src_dict)
        name = d.pop("name")

        incident_count = d.pop("incident_count", UNSET)

        def _parse_last_incident(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_incident_type_0 = datetime.datetime.fromisoformat(data)

                return last_incident_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_incident = _parse_last_incident(d.pop("last_incident", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: ServiceNodeMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ServiceNodeMetadata.from_dict(_metadata)

        status = d.pop("status", UNSET)

        type_ = d.pop("type", UNSET)

        service_node = cls(
            name=name,
            incident_count=incident_count,
            last_incident=last_incident,
            metadata=metadata,
            status=status,
            type_=type_,
        )

        service_node.additional_properties = d
        return service_node

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
