from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_request_context_type_0 import ChatRequestContextType0


T = TypeVar("T", bound="ChatRequest")


@_attrs_define
class ChatRequest:
    """Request to send a chat message.

    Example:
        {'context': {'error_rate': 0.15, 'service': 'payment-service'}, 'conversation_id': 'conv-123',
            'enable_thinking': True, 'message': 'Why is the payment service returning 503 errors?'}

    Attributes:
        message (str): User message
        context (ChatRequestContextType0 | None | Unset): Additional context (incident data, telemetry, etc.)
        conversation_id (None | str | Unset): Continue existing conversation
        enable_thinking (bool | Unset): Enable extended thinking mode for complex queries Default: False.
    """

    message: str
    context: ChatRequestContextType0 | None | Unset = UNSET
    conversation_id: None | str | Unset = UNSET
    enable_thinking: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.chat_request_context_type_0 import (
            ChatRequestContextType0,  # noqa: PLC0415
        )

        message = self.message

        context: dict[str, Any] | None | Unset
        if isinstance(self.context, Unset):
            context = UNSET
        elif isinstance(self.context, ChatRequestContextType0):
            context = self.context.to_dict()
        else:
            context = self.context

        conversation_id: None | str | Unset
        if isinstance(self.conversation_id, Unset):
            conversation_id = UNSET
        else:
            conversation_id = self.conversation_id

        enable_thinking = self.enable_thinking

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
            }
        )
        if context is not UNSET:
            field_dict["context"] = context
        if conversation_id is not UNSET:
            field_dict["conversation_id"] = conversation_id
        if enable_thinking is not UNSET:
            field_dict["enable_thinking"] = enable_thinking

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_request_context_type_0 import (
            ChatRequestContextType0,  # noqa: PLC0415
        )

        d = dict(src_dict)
        message = d.pop("message")

        def _parse_context(data: object) -> ChatRequestContextType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                context_type_0 = ChatRequestContextType0.from_dict(data)

                return context_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChatRequestContextType0 | None | Unset, data)

        context = _parse_context(d.pop("context", UNSET))

        def _parse_conversation_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        conversation_id = _parse_conversation_id(d.pop("conversation_id", UNSET))

        enable_thinking = d.pop("enable_thinking", UNSET)

        chat_request = cls(
            message=message,
            context=context,
            conversation_id=conversation_id,
            enable_thinking=enable_thinking,
        )

        chat_request.additional_properties = d
        return chat_request

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
