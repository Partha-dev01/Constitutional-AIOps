from enum import StrEnum


class ActionStatus(StrEnum):
    APPROVED = "approved"
    AWAITING_APPROVAL = "awaiting_approval"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXECUTING = "executing"
    EXPIRED = "expired"
    FAILED = "failed"
    PENDING = "pending"
    REJECTED = "rejected"
    VALIDATING = "validating"

    def __str__(self) -> str:
        return str(self.value)
