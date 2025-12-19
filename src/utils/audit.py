"""
Constitutional AIOps - Audit Logging System

Comprehensive audit logging for all system actions, decisions, and changes.
Provides traceability for Constitutional AI decisions and human approvals.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import uuid

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of auditable events."""
    # Incidents
    INCIDENT_CREATED = "incident.created"
    INCIDENT_UPDATED = "incident.updated"
    INCIDENT_RESOLVED = "incident.resolved"
    INCIDENT_CLOSED = "incident.closed"
    INCIDENT_ANALYZED = "incident.analyzed"

    # Actions
    ACTION_CREATED = "action.created"
    ACTION_VALIDATED = "action.validated"
    ACTION_APPROVED = "action.approved"
    ACTION_REJECTED = "action.rejected"
    ACTION_EXECUTED = "action.executed"
    ACTION_FAILED = "action.failed"
    ACTION_CANCELLED = "action.cancelled"

    # Constitutional AI
    CONSTITUTIONAL_VALIDATION = "constitutional.validation"
    CONSTITUTIONAL_VIOLATION = "constitutional.violation"
    CONSTITUTIONAL_OVERRIDE = "constitutional.override"

    # Tools
    TOOL_INVOKED = "tool.invoked"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"

    # System
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_CONFIG_CHANGE = "system.config_change"

    # User
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_ACTION = "user.action"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Audit event record.

    Contains all information about an auditable action in the system.
    """
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    severity: AuditSeverity

    # Actor information
    actor_type: str  # "system", "user", "agent"
    actor_id: str

    # Resource information
    resource_type: Optional[str] = None  # "incident", "action", "service"
    resource_id: Optional[str] = None

    # Event details
    description: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    # Constitutional AI context
    constitutional_context: Optional[dict[str, Any]] = None

    # Outcome
    outcome: str = "success"  # "success", "failure", "pending"
    error_message: Optional[str] = None

    # Metadata
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Audit logging system.

    Logs all auditable events to multiple destinations:
    - File (JSON lines format)
    - Standard logging
    - Optional external systems (Elasticsearch, etc.)
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        retention_days: int = 90,
    ):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit log files
            retention_days: Days to retain audit logs
        """
        self.log_dir = log_dir or Path("logs/audit")
        self.retention_days = retention_days
        self._ensure_log_dir()

        logger.info(f"AuditLogger initialized, log_dir={self.log_dir}")

    def _ensure_log_dir(self):
        """Ensure log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self) -> Path:
        """Get current log file path."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_dir / f"audit-{date_str}.jsonl"

    def log(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: Audit event to log
        """
        # Log to file
        log_file = self._get_log_file()
        with open(log_file, "a") as f:
            f.write(event.to_json() + "\n")

        # Log to standard logging
        log_level = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }.get(event.severity, logging.INFO)

        logger.log(
            log_level,
            f"AUDIT: [{event.event_type.value}] {event.description}",
            extra={"audit_event": event.to_dict()},
        )

    def log_incident_created(
        self,
        incident_id: str,
        title: str,
        severity: str,
        actor_id: str = "system",
        details: Optional[dict] = None,
    ) -> AuditEvent:
        """Log incident creation."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.INCIDENT_CREATED,
            timestamp=datetime.utcnow(),
            severity=AuditSeverity.INFO,
            actor_type="system" if actor_id == "system" else "user",
            actor_id=actor_id,
            resource_type="incident",
            resource_id=incident_id,
            description=f"Incident created: {title}",
            details={"title": title, "severity": severity, **(details or {})},
        )
        self.log(event)
        return event

    def log_action_created(
        self,
        action_id: str,
        action_type: str,
        target_service: str,
        confidence: float,
        actor_id: str = "system",
    ) -> AuditEvent:
        """Log action creation."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.ACTION_CREATED,
            timestamp=datetime.utcnow(),
            severity=AuditSeverity.INFO,
            actor_type="system" if actor_id == "system" else "user",
            actor_id=actor_id,
            resource_type="action",
            resource_id=action_id,
            description=f"Action created: {action_type} on {target_service}",
            details={
                "action_type": action_type,
                "target_service": target_service,
                "confidence": confidence,
            },
        )
        self.log(event)
        return event

    def log_constitutional_validation(
        self,
        action_id: str,
        passed: bool,
        authorization_level: str,
        violations: list[dict],
        warnings: list[str],
        explanation: str,
    ) -> AuditEvent:
        """Log Constitutional AI validation result."""
        severity = AuditSeverity.INFO
        if not passed:
            severity = AuditSeverity.WARNING
        if violations:
            severity = AuditSeverity.ERROR

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.CONSTITUTIONAL_VALIDATION,
            timestamp=datetime.utcnow(),
            severity=severity,
            actor_type="agent",
            actor_id="constitutional-ai",
            resource_type="action",
            resource_id=action_id,
            description=f"Constitutional validation: {'passed' if passed else 'failed'}",
            constitutional_context={
                "passed": passed,
                "authorization_level": authorization_level,
                "violations": violations,
                "warnings": warnings,
                "explanation": explanation,
            },
            outcome="success" if passed else "failure",
        )
        self.log(event)
        return event

    def log_action_approved(
        self,
        action_id: str,
        approved_by: str,
        comments: Optional[str] = None,
    ) -> AuditEvent:
        """Log action approval."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.ACTION_APPROVED,
            timestamp=datetime.utcnow(),
            severity=AuditSeverity.INFO,
            actor_type="user",
            actor_id=approved_by,
            resource_type="action",
            resource_id=action_id,
            description=f"Action approved by {approved_by}",
            details={"comments": comments},
        )
        self.log(event)
        return event

    def log_action_rejected(
        self,
        action_id: str,
        rejected_by: str,
        reason: Optional[str] = None,
    ) -> AuditEvent:
        """Log action rejection."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.ACTION_REJECTED,
            timestamp=datetime.utcnow(),
            severity=AuditSeverity.WARNING,
            actor_type="user",
            actor_id=rejected_by,
            resource_type="action",
            resource_id=action_id,
            description=f"Action rejected by {rejected_by}",
            details={"reason": reason},
        )
        self.log(event)
        return event

    def log_action_executed(
        self,
        action_id: str,
        success: bool,
        duration_ms: float,
        output: Optional[str] = None,
        error: Optional[str] = None,
    ) -> AuditEvent:
        """Log action execution."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.ACTION_EXECUTED if success else AuditEventType.ACTION_FAILED,
            timestamp=datetime.utcnow(),
            severity=AuditSeverity.INFO if success else AuditSeverity.ERROR,
            actor_type="system",
            actor_id="executor",
            resource_type="action",
            resource_id=action_id,
            description=f"Action execution {'completed' if success else 'failed'}",
            details={
                "duration_ms": duration_ms,
                "output": output,
            },
            outcome="success" if success else "failure",
            error_message=error,
        )
        self.log(event)
        return event

    def log_tool_invocation(
        self,
        tool_name: str,
        parameters: dict,
        actor_id: str = "system",
        context: Optional[dict] = None,
    ) -> AuditEvent:
        """Log tool invocation."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.TOOL_INVOKED,
            timestamp=datetime.utcnow(),
            severity=AuditSeverity.INFO,
            actor_type="system",
            actor_id=actor_id,
            resource_type="tool",
            resource_id=tool_name,
            description=f"Tool invoked: {tool_name}",
            details={"parameters": parameters, "context": context},
        )
        self.log(event)
        return event

    def log_system_event(
        self,
        event_type: AuditEventType,
        description: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[dict] = None,
    ) -> AuditEvent:
        """Log system event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            severity=severity,
            actor_type="system",
            actor_id="constitutional-aiops",
            description=description,
            details=details or {},
        )
        self.log(event)
        return event

    def query_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[list[AuditEventType]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """
        Query audit events.

        Args:
            start_date: Start of time range
            end_date: End of time range
            event_types: Filter by event types
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            actor_id: Filter by actor ID
            limit: Maximum events to return

        Returns:
            List of matching audit events
        """
        events = []

        # Determine which log files to read
        if start_date is None:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if end_date is None:
            end_date = datetime.utcnow()

        current_date = start_date
        while current_date <= end_date:
            log_file = self.log_dir / f"audit-{current_date.strftime('%Y-%m-%d')}.jsonl"
            if log_file.exists():
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            event_time = datetime.fromisoformat(data["timestamp"])

                            # Apply filters
                            if event_time < start_date or event_time > end_date:
                                continue
                            if event_types and data["event_type"] not in [et.value for et in event_types]:
                                continue
                            if resource_type and data.get("resource_type") != resource_type:
                                continue
                            if resource_id and data.get("resource_id") != resource_id:
                                continue
                            if actor_id and data.get("actor_id") != actor_id:
                                continue

                            events.append(data)
                            if len(events) >= limit:
                                break
                        except (json.JSONDecodeError, KeyError):
                            continue

            current_date = current_date.replace(day=current_date.day + 1)
            if len(events) >= limit:
                break

        return events[:limit]


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def set_audit_logger(audit_logger: AuditLogger) -> None:
    """Set the global audit logger instance."""
    global _audit_logger
    _audit_logger = audit_logger


__all__ = [
    "AuditEventType",
    "AuditSeverity",
    "AuditEvent",
    "AuditLogger",
    "get_audit_logger",
    "set_audit_logger",
]
