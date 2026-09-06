from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.chat_message import ChatMessage
    from ..models.chat_response_metadata_type_0 import ChatResponseMetadataType0
    from ..models.chat_response_proposed_action_type_0 import (
        ChatResponseProposedActionType0,
    )


T = TypeVar("T", bound="ChatResponse")


@_attrs_define
class ChatResponse:
    """Response from chat endpoint.

    Example:
        {'confidence': 0.85, 'conversation_id': 'conv-123', 'message': {'content': 'The payment service is returning 503
            errors due to...', 'role': 'assistant', 'timestamp': '2025-12-14T10:30:05Z'}, 'related_incidents':
            ['INC-2024-001', 'INC-2024-012'], 'suggested_actions': ['Scale up payment-service', 'Check database
            connections']}

    Attributes:
        conversation_id (str): Conversation identifier
        message (ChatMessage): Single chat message. Example: {'content': 'What caused the spike in CPU usage on prod-
            api-1?', 'role': 'user', 'timestamp': '2025-12-14T10:30:00Z'}.
        confidence (float | None | Unset): Confidence in response; null when the agent declines an off-domain request
        metadata (ChatResponseMetadataType0 | None | Unset): Additional metadata
        proposed_action (ChatResponseProposedActionType0 | None | Unset): AI-proposed remediation action riding the chat
            response (approve/auto modes only; omitted entirely in diagnose mode). Shape: {id, tool_name,
            parameters{service_name, reason}, target, title, rationale, mode, status, verdict, execution_result}.
        related_incidents (list[str] | None | Unset): Related incident IDs from memory
        suggested_actions (list[str] | None | Unset): Suggested follow-up actions
    """

    conversation_id: str
    message: ChatMessage
    confidence: float | None | Unset = UNSET
    metadata: ChatResponseMetadataType0 | None | Unset = UNSET
    proposed_action: ChatResponseProposedActionType0 | None | Unset = UNSET
    related_incidents: list[str] | None | Unset = UNSET
    suggested_actions: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.chat_response_metadata_type_0 import (
            ChatResponseMetadataType0,  # noqa: PLC0415
        )
        from ..models.chat_response_proposed_action_type_0 import (
            ChatResponseProposedActionType0,  # noqa: PLC0415
        )

        conversation_id = self.conversation_id

        message = self.message.to_dict()

        confidence: float | None | Unset
        if isinstance(self.confidence, Unset):
            confidence = UNSET
        else:
            confidence = self.confidence

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ChatResponseMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        proposed_action: dict[str, Any] | None | Unset
        if isinstance(self.proposed_action, Unset):
            proposed_action = UNSET
        elif isinstance(self.proposed_action, ChatResponseProposedActionType0):
            proposed_action = self.proposed_action.to_dict()
        else:
            proposed_action = self.proposed_action

        related_incidents: list[str] | None | Unset
        if isinstance(self.related_incidents, Unset):
            related_incidents = UNSET
        elif isinstance(self.related_incidents, list):
            related_incidents = self.related_incidents

        else:
            related_incidents = self.related_incidents

        suggested_actions: list[str] | None | Unset
        if isinstance(self.suggested_actions, Unset):
            suggested_actions = UNSET
        elif isinstance(self.suggested_actions, list):
            suggested_actions = self.suggested_actions

        else:
            suggested_actions = self.suggested_actions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "conversation_id": conversation_id,
                "message": message,
            }
        )
        if confidence is not UNSET:
            field_dict["confidence"] = confidence
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if proposed_action is not UNSET:
            field_dict["proposed_action"] = proposed_action
        if related_incidents is not UNSET:
            field_dict["related_incidents"] = related_incidents
        if suggested_actions is not UNSET:
            field_dict["suggested_actions"] = suggested_actions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.chat_message import ChatMessage  # noqa: PLC0415
        from ..models.chat_response_metadata_type_0 import (
            ChatResponseMetadataType0,  # noqa: PLC0415
        )
        from ..models.chat_response_proposed_action_type_0 import (
            ChatResponseProposedActionType0,  # noqa: PLC0415
        )

        d = dict(src_dict)
        conversation_id = d.pop("conversation_id")

        message = ChatMessage.from_dict(d.pop("message"))

        def _parse_confidence(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        confidence = _parse_confidence(d.pop("confidence", UNSET))

        def _parse_metadata(data: object) -> ChatResponseMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ChatResponseMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChatResponseMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_proposed_action(
            data: object,
        ) -> ChatResponseProposedActionType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                proposed_action_type_0 = ChatResponseProposedActionType0.from_dict(data)

                return proposed_action_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChatResponseProposedActionType0 | None | Unset, data)

        proposed_action = _parse_proposed_action(d.pop("proposed_action", UNSET))

        def _parse_related_incidents(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                related_incidents_type_0 = cast(list[str], data)

                return related_incidents_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        related_incidents = _parse_related_incidents(d.pop("related_incidents", UNSET))

        def _parse_suggested_actions(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                suggested_actions_type_0 = cast(list[str], data)

                return suggested_actions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        suggested_actions = _parse_suggested_actions(d.pop("suggested_actions", UNSET))

        chat_response = cls(
            conversation_id=conversation_id,
            message=message,
            confidence=confidence,
            metadata=metadata,
            proposed_action=proposed_action,
            related_incidents=related_incidents,
            suggested_actions=suggested_actions,
        )

        chat_response.additional_properties = d
        return chat_response

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
