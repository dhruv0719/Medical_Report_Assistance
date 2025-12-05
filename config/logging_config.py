# config/logging_config.py
"""
Centralized logging configuration using Loguru.
Provides structured logging with rotation, retention, and multiple outputs.
"""

import sys
from pathlib import Path
from loguru import logger
from config.settings import Paths, LogConfig

def setup_logging():
    """
    Configure logging for the entire application.
    Call this once at application startup.
    """

    # Remove default logger
    logger.remove()
    
    # Console output (pretty, colored)
    logger.add(
        sys.stdout,
        format=LogConfig.LOG_FORMAT,
        level=LogConfig.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Application log (all info and above)
    logger.add(
        Paths.APP_LOG,
        format=LogConfig.LOG_FORMAT,
        level="INFO",
        rotation=LogConfig.LOG_ROTATION,
        retention=LogConfig.LOG_RETENTION,
        compression="zip",
        enqueue=True,  # Thread-safe
    )
    
    # Error log (errors only)
    logger.add(
        Paths.ERROR_LOG,
        format=LogConfig.LOG_FORMAT,
        level="ERROR",
        rotation=LogConfig.LOG_ROTATION,
        retention=LogConfig.LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    
    # Audit log (separate, structured)
    logger.add(
        Paths.AUDIT_LOG,
        format="{time:YYYY-MM-DD HH:mm:ss} | {extra[event_type]} | {message}",
        level="INFO",
        rotation=LogConfig.LOG_ROTATION,
        retention="1 year",  # Keep audit logs longer
        compression="zip",
        enqueue=True,
        filter=lambda record: "audit" in record["extra"],
    )
    
    logger.info("✅ Logging configured successfully")


def get_logger(name: str):
    """
    Get a logger instance with a specific name.
    
    Args:
        name: Logger name (usually __name__ of the module)
        
    Returns:
        Configured logger instance
    """
    return logger.bind(name=name)


class AuditLogger:
    """
    Specialized logger for audit trail (HIPAA compliance).
    Logs all system interactions in a structured format.
    """
    
    def __init__(self):
        self.logger = logger.bind(audit=True)
    
    def log(self, event_type: str, message: str, **kwargs):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (upload, parse, llm_call, alert, etc.)
            message: Human-readable message
            **kwargs: Additional structured data
        """
        self.logger.bind(event_type=event_type).info(message, **kwargs)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "setup_logging",
    "get_logger",
    "AuditLogger",
    "logger",
]