"""Error handling utilities for user-friendly error messages."""

from __future__ import annotations

import logging
from typing import Optional
from PyQt6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger(__name__)


def show_error(
    parent: Optional[QWidget],
    title: str,
    message: str,
    details: Optional[str] = None,
    recovery_suggestion: Optional[str] = None,
) -> None:
    """
    Show a user-friendly error message with recovery suggestions.
    
    Args:
        parent: Parent widget
        title: Error title
        message: User-friendly error message
        details: Optional technical details (logged but not shown to user)
        recovery_suggestion: Optional recovery suggestion to display
    """
    if details:
        logger.error("%s: %s\nDetails: %s", title, message, details, exc_info=True)
    else:
        logger.error("%s: %s", title, message)
    
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    
    # Combine message with recovery suggestion if provided
    full_message = message
    if recovery_suggestion:
        full_message = f"{message}\n\n💡 Suggestion: {recovery_suggestion}"
    
    msg.setText(full_message)
    
    if details:
        msg.setDetailedText(details)
    
    msg.exec()


def show_warning(
    parent: Optional[QWidget],
    title: str,
    message: str,
) -> None:
    """
    Show a user-friendly warning message.
    
    Args:
        parent: Parent widget
        title: Warning title
        message: User-friendly warning message
    """
    logger.warning("%s: %s", title, message)
    
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_info(
    parent: Optional[QWidget],
    title: str,
    message: str,
) -> None:
    """
    Show an informational message.
    
    Args:
        parent: Parent widget
        title: Info title
        message: Informational message
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def format_file_error(error: Exception, file_path: str, operation: str) -> tuple[str, Optional[str]]:
    """
    Format a file operation error message with recovery suggestion.
    
    Args:
        error: The exception
        file_path: Path to the file
        operation: Operation being performed (e.g., "save", "load", "delete")
        
    Returns:
        Tuple of (error message, recovery suggestion)
    """
    error_type = type(error).__name__
    error_str = str(error).lower()
    
    if "Permission" in error_type or "permission" in error_str:
        suggestion = "Close the file if it's open in another program, check file permissions, or try running as administrator."
        return (
            f"Cannot {operation} file: Permission denied.\n\nFile: {file_path}",
            suggestion
        )
    
    if "NotFound" in error_type or "not found" in error_str:
        suggestion = "Check if the file was moved or deleted. Verify the file path is correct."
        return (
            f"Cannot {operation} file: File not found.\n\nFile: {file_path}",
            suggestion
        )
    
    if "Disk" in error_type or "disk" in error_str or "space" in error_str:
        suggestion = "Free up disk space by deleting unnecessary files or moving files to another drive."
        return (
            f"Cannot {operation} file: Insufficient disk space.\n\nFile: {file_path}",
            suggestion
        )
    
    return (f"Cannot {operation} file: {str(error)}\n\nFile: {file_path}", None)


def format_database_error(error: Exception, operation: str) -> tuple[str, Optional[str]]:
    """
    Format a database operation error message with recovery suggestion.
    
    Args:
        error: The exception
        operation: Operation being performed (e.g., "save", "load", "delete")
        
    Returns:
        Tuple of (error message, recovery suggestion)
    """
    error_type = type(error).__name__
    error_msg = str(error).lower()
    
    if "IntegrityError" in error_type or "unique constraint" in error_msg:
        suggestion = "The record you're trying to create already exists. Try editing the existing record instead."
        return (
            f"Cannot {operation} data: Duplicate entry detected.\n\nThis record already exists in the database.",
            suggestion
        )
    
    if "OperationalError" in error_type or "locked" in error_msg:
        suggestion = "Close any other programs that might be using the database, then try again."
        return (
            f"Cannot {operation} data: Database is locked.\n\nAnother process may be using the database.",
            suggestion
        )
    
    if "NoSuchTable" in error_type or "no such table" in error_msg:
        suggestion = "The database structure may be corrupted. Try restarting the application or restoring from backup."
        return (
            f"Cannot {operation} data: Database structure error.\n\nThe database may need to be reinitialized.",
            suggestion
        )
    
    return (f"Cannot {operation} data: {error_msg}\n\nPlease try again.", "If the problem persists, restart the application or contact support.")


def format_network_error(error: Exception, operation: str) -> str:
    """
    Format a network operation error message.
    
    Args:
        error: The exception
        operation: Operation being performed (e.g., "connect", "download", "upload")
        
    Returns:
        User-friendly error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if "ConnectionError" in error_type or "timeout" in error_msg.lower():
        return f"Cannot {operation}: Connection failed.\n\nPlease check your internet connection and try again."
    
    if "Timeout" in error_type:
        return f"Cannot {operation}: Request timed out.\n\nThe server may be slow or unavailable. Please try again."
    
    return f"Cannot {operation}: {error_msg}\n\nPlease check your connection and try again."

