"""
Structured logging configuration for the Parcel Feasibility Engine.

This module provides centralized logging configuration with support for:
- JSON and text log formats
- Different log levels per environment
- Request/response logging
- Rule decision logging for debugging
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Custom text formatter for human-readable logs."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging() -> None:
    """
    Configure application-wide logging based on settings.

    Uses JSON format in production, text format in development.
    """
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create formatter based on configuration
    if settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the module (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class DecisionLogger:
    """
    Helper class for logging rule decisions in debug mode.

    This enables detailed tracing of eligibility checks and rule applications
    for debugging and transparency.
    """

    def __init__(self, parcel_apn: str, logger: Optional[logging.Logger] = None):
        """
        Initialize decision logger for a specific parcel.

        Args:
            parcel_apn: APN of the parcel being analyzed
            logger: Optional logger instance (creates new one if not provided)
        """
        self.parcel_apn = parcel_apn
        self.logger = logger or get_logger("rules.decisions")
        self.decisions: list[Dict[str, Any]] = []

    def log_decision(
        self,
        rule_name: str,
        decision: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a rule decision.

        Args:
            rule_name: Name of the rule being evaluated
            decision: Decision outcome (e.g., "eligible", "ineligible", "applied")
            reason: Human-readable reason for the decision
            details: Optional additional details
        """
        decision_record = {
            "parcel_apn": self.parcel_apn,
            "rule": rule_name,
            "decision": decision,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if details:
            decision_record["details"] = details

        self.decisions.append(decision_record)

        self.logger.info(
            f"Rule decision: {rule_name} - {decision}",
            extra={
                "parcel_apn": self.parcel_apn,
                "rule": rule_name,
                "decision": decision,
                "reason": reason,
                "details": details,
            }
        )

    def log_eligibility_check(
        self,
        rule_name: str,
        eligible: bool,
        reason: str,
        criteria: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an eligibility check result.

        Args:
            rule_name: Name of the rule
            eligible: Whether the parcel is eligible
            reason: Reason for eligibility/ineligibility
            criteria: Optional criteria evaluated
        """
        self.log_decision(
            rule_name=rule_name,
            decision="eligible" if eligible else "ineligible",
            reason=reason,
            details={"criteria": criteria} if criteria else None
        )

    def log_standard_application(
        self,
        rule_name: str,
        standard_name: str,
        value: Any,
        calculation: Optional[str] = None
    ) -> None:
        """
        Log application of a development standard.

        Args:
            rule_name: Name of the rule
            standard_name: Name of the standard (e.g., "max_height", "setback")
            value: Applied value
            calculation: Optional calculation explanation
        """
        self.log_decision(
            rule_name=rule_name,
            decision="applied",
            reason=f"Applied {standard_name}: {value}",
            details={
                "standard": standard_name,
                "value": value,
                "calculation": calculation,
            }
        )

    def get_decisions(self) -> list[Dict[str, Any]]:
        """Get all logged decisions."""
        return self.decisions

    def get_decision_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all decisions.

        Returns:
            Summary with counts by decision type
        """
        summary = {
            "total_decisions": len(self.decisions),
            "by_type": {},
            "by_rule": {},
        }

        for decision in self.decisions:
            decision_type = decision["decision"]
            rule = decision["rule"]

            summary["by_type"][decision_type] = summary["by_type"].get(decision_type, 0) + 1
            summary["by_rule"][rule] = summary["by_rule"].get(rule, 0) + 1

        return summary
