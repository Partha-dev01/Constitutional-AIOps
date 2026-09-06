from enum import StrEnum


class TelegramAlertingPublicMinseverity(StrEnum):
    CRITICAL = "critical"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
