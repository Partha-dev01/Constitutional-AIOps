from enum import StrEnum


class IncidentStatus(StrEnum):
    ANALYZING = "analyzing"
    CLOSED = "closed"
    DETECTING = "detecting"
    PENDING_APPROVAL = "pending_approval"
    REMEDIATING = "remediating"
    RESOLVED = "resolved"

    def __str__(self) -> str:
        return str(self.value)
