from enum import StrEnum


class RemediationSettingsModelAutoToolAllowlistItem(StrEnum):
    RESTART_SERVICE = "restart_service"
    SCALE_SERVICE = "scale_service"

    def __str__(self) -> str:
        return str(self.value)
