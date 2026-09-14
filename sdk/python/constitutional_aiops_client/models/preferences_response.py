from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ai_widgets_prefs import AiWidgetsPrefs
    from ..models.preferences_response_budget import PreferencesResponseBudget


T = TypeVar("T", bound="PreferencesResponse")


@_attrs_define
class PreferencesResponse:
    """Current opt-in state plus the fence budget snapshot for the UI.

    Attributes:
        ai_widgets (AiWidgetsPrefs): The per-user opt-in state for the LLM insight widgets.
        budget (PreferencesResponseBudget | Unset):
    """

    ai_widgets: AiWidgetsPrefs
    budget: PreferencesResponseBudget | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ai_widgets = self.ai_widgets.to_dict()

        budget: dict[str, Any] | Unset = UNSET
        if not isinstance(self.budget, Unset):
            budget = self.budget.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "aiWidgets": ai_widgets,
            }
        )
        if budget is not UNSET:
            field_dict["budget"] = budget

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ai_widgets_prefs import AiWidgetsPrefs  # noqa: PLC0415
        from ..models.preferences_response_budget import PreferencesResponseBudget  # noqa: PLC0415

        d = dict(src_dict)
        ai_widgets = AiWidgetsPrefs.from_dict(d.pop("aiWidgets"))

        _budget = d.pop("budget", UNSET)
        budget: PreferencesResponseBudget | Unset
        if isinstance(_budget, Unset):
            budget = UNSET
        else:
            budget = PreferencesResponseBudget.from_dict(_budget)

        preferences_response = cls(
            ai_widgets=ai_widgets,
            budget=budget,
        )

        preferences_response.additional_properties = d
        return preferences_response

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
