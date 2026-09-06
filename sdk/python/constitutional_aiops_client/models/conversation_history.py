from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_message import ChatMessage
    from ..models.conversation_history_context_type_0 import (
        ConversationHistoryContextType0,
    )


T = TypeVar("T", bound="ConversationHistory")


@_attrs_define
class ConversationHistory:
    """Full conversation history.

    Example:
        {'conversation_id': 'conv-123', 'created_at': '2025-12-14T10:00:00Z', 'messages': [{'content': 'Hello', 'role':
            'user'}, {'content': 'Hello! How can I help?', 'role': 'assistant'}], 'updated_at': '2025-12-14T10:30:05Z'}

    Attributes:
        conversation_id (str):
        created_at (datetime.datetime):
        messages (list[ChatMessage]):
        updated_at (datetime.datetime):
        context (ConversationHistoryContextType0 | None | Unset):
        owner (None | str | Unset): Username that owns this conversation; None for legacy/global ones
    """

    conversation_id: str
    created_at: datetime.datetime
    messages: list[ChatMessage]
    updated_at: datetime.datetime
    context: ConversationHistoryContextType0 | None | Unset = UNSET
    owner: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.conversation_history_context_type_0 import (
            ConversationHistoryContextType0,  # noqa: PLC0415
        )

        conversation_id = self.conversation_id

        created_at = self.created_at.isoformat()

        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        updated_at = self.updated_at.isoformat()

        context: dict[str, Any] | None | Unset
        if isinstance(self.context, Unset):
            context = UNSET
        elif isinstance(self.context, ConversationHistoryContextType0):
            context = self.context.to_dict()
        else:
            context = self.context

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "conversation_id": conversation_id,
                "created_at": created_at,
                "messages": messages,
                "updated_at": updated_at,
            }
        )
        if context is not UNSET:
            field_dict["context"] = context
        if owner is not UNSET:
            field_dict["owner"] = owner

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_message import ChatMessage  # noqa: PLC0415
        from ..models.conversation_history_context_type_0 import (
            ConversationHistoryContextType0,  # noqa: PLC0415
        )

        d = dict(src_dict)
        conversation_id = d.pop("conversation_id")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = ChatMessage.from_dict(messages_item_data)

            messages.append(messages_item)

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_context(
            data: object,
        ) -> ConversationHistoryContextType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                context_type_0 = ConversationHistoryContextType0.from_dict(data)

                return context_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ConversationHistoryContextType0 | None | Unset, data)

        context = _parse_context(d.pop("context", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        conversation_history = cls(
            conversation_id=conversation_id,
            created_at=created_at,
            messages=messages,
            updated_at=updated_at,
            context=context,
            owner=owner,
        )

        conversation_history.additional_properties = d
        return conversation_history

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
