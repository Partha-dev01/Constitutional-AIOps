from enum import StrEnum


class NotificationSettingsModelWebhookminseverity(StrEnum):
    CRITICAL = "critical"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
