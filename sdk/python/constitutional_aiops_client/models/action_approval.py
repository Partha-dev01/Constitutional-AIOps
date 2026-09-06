from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.action_approval_modifications_type_0 import (
        ActionApprovalModificationsType0,
    )


T = TypeVar("T", bound="ActionApproval")


@_attrs_define
class ActionApproval:
    """Human approval for an action.

    Example:
        {'approved': True, 'approved_by': 'operator@company.com', 'comments': 'Approved - customer impact acceptable'}

    Attributes:
        approved (bool): Whether action is approved
        approved_by (str): Approver username or ID
        comments (None | str | Unset):
        modifications (ActionApprovalModificationsType0 | None | Unset): Optional modifications to action parameters
    """

    approved: bool
    approved_by: str
    comments: None | str | Unset = UNSET
    modifications: ActionApprovalModificationsType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.action_approval_modifications_type_0 import (
            ActionApprovalModificationsType0,  # noqa: PLC0415
        )

        approved = self.approved

        approved_by = self.approved_by

        comments: None | str | Unset
        if isinstance(self.comments, Unset):
            comments = UNSET
        else:
            comments = self.comments

        modifications: dict[str, Any] | None | Unset
        if isinstance(self.modifications, Unset):
            modifications = UNSET
        elif isinstance(self.modifications, ActionApprovalModificationsType0):
            modifications = self.modifications.to_dict()
        else:
            modifications = self.modifications

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "approved": approved,
                "approved_by": approved_by,
            }
        )
        if comments is not UNSET:
            field_dict["comments"] = comments
        if modifications is not UNSET:
            field_dict["modifications"] = modifications

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.action_approval_modifications_type_0 import (
            ActionApprovalModificationsType0,  # noqa: PLC0415
        )

        d = dict(src_dict)
        approved = d.pop("approved")

        approved_by = d.pop("approved_by")

        def _parse_comments(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comments = _parse_comments(d.pop("comments", UNSET))

        def _parse_modifications(
            data: object,
        ) -> ActionApprovalModificationsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                modifications_type_0 = ActionApprovalModificationsType0.from_dict(data)

                return modifications_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ActionApprovalModificationsType0 | None | Unset, data)

        modifications = _parse_modifications(d.pop("modifications", UNSET))

        action_approval = cls(
            approved=approved,
            approved_by=approved_by,
            comments=comments,
            modifications=modifications,
        )

        action_approval.additional_properties = d
        return action_approval

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
