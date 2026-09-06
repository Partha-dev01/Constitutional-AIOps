from enum import StrEnum


class ServingModeStatusSwapStatus(StrEnum):
    ERROR = "error"
    IDLE = "idle"
    PENDING = "pending"
    SWAPPING = "swapping"

    def __str__(self) -> str:
        return str(self.value)
