from enum import StrEnum


class RemediationSettingsModelMode(StrEnum):
    APPROVE = "approve"
    AUTO = "auto"
    DIAGNOSE = "diagnose"

    def __str__(self) -> str:
        return str(self.value)
