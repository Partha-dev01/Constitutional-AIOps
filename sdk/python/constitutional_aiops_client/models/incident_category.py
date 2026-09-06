from enum import StrEnum


class IncidentCategory(StrEnum):
    AVAILABILITY = "availability"
    CONFIGURATION = "configuration"
    ERROR = "error"
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    SECURITY = "security"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
