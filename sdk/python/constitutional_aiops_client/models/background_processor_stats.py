from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BackgroundProcessorStats")


@_attrs_define
class BackgroundProcessorStats:
    """Background telemetry processor statistics.

    Attributes:
        running (bool): Whether processor is running
        anomalies_detected (int | Unset): Total anomalies detected Default: 0.
        episodes_created (int | Unset): Episodes stored in graph Default: 0.
        errors (int | Unset): Processing errors Default: 0.
        escalations_to_reasoning (int | Unset): Times escalated to Reasoning Agent Default: 0.
        last_run (None | str | Unset): Timestamp of last processing cycle
        processing_interval_seconds (int | Unset): Seconds between cycles Default: 30.
        services_monitored (int | Unset): Number of services being monitored Default: 0.
        telemetry_processed (int | Unset): Total telemetry windows processed Default: 0.
        total_cycles (int | Unset): Total processing cycles completed Default: 0.
    """

    running: bool
    anomalies_detected: int | Unset = 0
    episodes_created: int | Unset = 0
    errors: int | Unset = 0
    escalations_to_reasoning: int | Unset = 0
    last_run: None | str | Unset = UNSET
    processing_interval_seconds: int | Unset = 30
    services_monitored: int | Unset = 0
    telemetry_processed: int | Unset = 0
    total_cycles: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        running = self.running

        anomalies_detected = self.anomalies_detected

        episodes_created = self.episodes_created

        errors = self.errors

        escalations_to_reasoning = self.escalations_to_reasoning

        last_run: None | str | Unset
        if isinstance(self.last_run, Unset):
            last_run = UNSET
        else:
            last_run = self.last_run

        processing_interval_seconds = self.processing_interval_seconds

        services_monitored = self.services_monitored

        telemetry_processed = self.telemetry_processed

        total_cycles = self.total_cycles

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "running": running,
            }
        )
        if anomalies_detected is not UNSET:
            field_dict["anomalies_detected"] = anomalies_detected
        if episodes_created is not UNSET:
            field_dict["episodes_created"] = episodes_created
        if errors is not UNSET:
            field_dict["errors"] = errors
        if escalations_to_reasoning is not UNSET:
            field_dict["escalations_to_reasoning"] = escalations_to_reasoning
        if last_run is not UNSET:
            field_dict["last_run"] = last_run
        if processing_interval_seconds is not UNSET:
            field_dict["processing_interval_seconds"] = processing_interval_seconds
        if services_monitored is not UNSET:
            field_dict["services_monitored"] = services_monitored
        if telemetry_processed is not UNSET:
            field_dict["telemetry_processed"] = telemetry_processed
        if total_cycles is not UNSET:
            field_dict["total_cycles"] = total_cycles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        running = d.pop("running")

        anomalies_detected = d.pop("anomalies_detected", UNSET)

        episodes_created = d.pop("episodes_created", UNSET)

        errors = d.pop("errors", UNSET)

        escalations_to_reasoning = d.pop("escalations_to_reasoning", UNSET)

        def _parse_last_run(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_run = _parse_last_run(d.pop("last_run", UNSET))

        processing_interval_seconds = d.pop("processing_interval_seconds", UNSET)

        services_monitored = d.pop("services_monitored", UNSET)

        telemetry_processed = d.pop("telemetry_processed", UNSET)

        total_cycles = d.pop("total_cycles", UNSET)

        background_processor_stats = cls(
            running=running,
            anomalies_detected=anomalies_detected,
            episodes_created=episodes_created,
            errors=errors,
            escalations_to_reasoning=escalations_to_reasoning,
            last_run=last_run,
            processing_interval_seconds=processing_interval_seconds,
            services_monitored=services_monitored,
            telemetry_processed=telemetry_processed,
            total_cycles=total_cycles,
        )

        background_processor_stats.additional_properties = d
        return background_processor_stats

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
