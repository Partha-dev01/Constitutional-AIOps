from enum import StrEnum


class MatrixAlertingPublicMinseverity(StrEnum):
    CRITICAL = "critical"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
