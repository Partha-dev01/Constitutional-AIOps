from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="OnboardingState")


@_attrs_define
class OnboardingState:
    """First-run wizard progress. ``step`` is the furthest step reached.

    Attributes:
        completed (bool | Unset):  Default: False.
        skipped (bool | Unset):  Default: False.
        step (int | Unset):  Default: 0.
    """

    completed: bool | Unset = False
    skipped: bool | Unset = False
    step: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        completed = self.completed

        skipped = self.skipped

        step = self.step

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if completed is not UNSET:
            field_dict["completed"] = completed
        if skipped is not UNSET:
            field_dict["skipped"] = skipped
        if step is not UNSET:
            field_dict["step"] = step

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        completed = d.pop("completed", UNSET)

        skipped = d.pop("skipped", UNSET)

        step = d.pop("step", UNSET)

        onboarding_state = cls(
            completed=completed,
            skipped=skipped,
            step=step,
        )

        onboarding_state.additional_properties = d
        return onboarding_state

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
