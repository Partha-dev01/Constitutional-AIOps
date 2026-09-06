from enum import StrEnum


class AuthorizationLevel(StrEnum):
    ALERT = "alert"
    APPROVAL = "approval"
    AUTOMATIC = "automatic"

    def __str__(self) -> str:
        return str(self.value)
