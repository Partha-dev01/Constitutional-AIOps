from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.chat_role import ChatRole
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_message_metadata_type_0 import ChatMessageMetadataType0


T = TypeVar("T", bound="ChatMessage")


@_attrs_define
class ChatMessage:
    """Single chat message.

    Example:
        {'content': 'What caused the spike in CPU usage on prod-api-1?', 'role': 'user', 'timestamp':
            '2025-12-14T10:30:00Z'}

    Attributes:
        content (str): Message content
        role (ChatRole): Chat message roles.
        metadata (ChatMessageMetadataType0 | None | Unset): Per-turn assistant metadata (confidence, suggested/related,
            tool results, proposed_action) persisted so a conversation reloaded from history can replay its reasoning
            timeline + insight cards. Null on user turns and on pre-existing conversations.
        timestamp (datetime.datetime | None | Unset):
    """

    content: str
    role: ChatRole
    metadata: ChatMessageMetadataType0 | None | Unset = UNSET
    timestamp: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.chat_message_metadata_type_0 import (
            ChatMessageMetadataType0,  # noqa: PLC0415
        )

        content = self.content

        role = self.role.value

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ChatMessageMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        timestamp: None | str | Unset
        if isinstance(self.timestamp, Unset):
            timestamp = UNSET
        elif isinstance(self.timestamp, datetime.datetime):
            timestamp = self.timestamp.isoformat()
        else:
            timestamp = self.timestamp

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
                "role": role,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_message_metadata_type_0 import (
            ChatMessageMetadataType0,  # noqa: PLC0415
        )

        d = dict(src_dict)
        content = d.pop("content")

        role = ChatRole(d.pop("role"))

        def _parse_metadata(data: object) -> ChatMessageMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ChatMessageMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChatMessageMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_timestamp(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                timestamp_type_0 = datetime.datetime.fromisoformat(data)

                return timestamp_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        timestamp = _parse_timestamp(d.pop("timestamp", UNSET))

        chat_message = cls(
            content=content,
            role=role,
            metadata=metadata,
            timestamp=timestamp,
        )

        chat_message.additional_properties = d
        return chat_message

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
