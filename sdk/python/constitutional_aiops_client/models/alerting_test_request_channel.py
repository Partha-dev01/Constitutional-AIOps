from enum import StrEnum


class AlertingTestRequestChannel(StrEnum):
    MATRIX = "matrix"
    TELEGRAM = "telegram"

    def __str__(self) -> str:
        return str(self.value)
