"""Undo/redo system for drawing operations on video canvas."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


@dataclass
class DrawingAction:
    """Represents a drawing action that can be undone/redone."""
    action_type: str  # "add_line", "remove_line", "change_color", "clear_all", "add_measurement", "remove_measurement"
    canvas_id: str  # "dtl" or "face"
    data: dict[str, Any]  # Action-specific data
    undo_func: Callable
    redo_func: Callable


class DrawingUndoRedoManager:
    """Manages undo/redo stack for drawing operations."""
    
    def __init__(self, max_stack_size: int = 100) -> None:
        """Initialize undo/redo manager.
        
        Args:
            max_stack_size: Maximum number of actions to keep in stack
        """
        self.undo_stack: list[DrawingAction] = []
        self.redo_stack: list[DrawingAction] = []
        self.max_stack_size = max_stack_size
    
    def push_action(self, action: DrawingAction) -> None:
        """Push an action onto the undo stack.
        
        Args:
            action: The drawing action to push
        """
        self.undo_stack.append(action)
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new action is pushed
        self.redo_stack.clear()
    
    def undo(self) -> Optional[DrawingAction]:
        """Undo the last action.
        
        Returns:
            The action that was undone, or None if stack is empty
        """
        if not self.undo_stack:
            return None
        
        action = self.undo_stack.pop()
        try:
            action.undo_func()
            self.redo_stack.append(action)
            return action
        except Exception as e:
            logger.error("Error undoing action: %s", e, exc_info=True)
            # Put action back on stack
            self.undo_stack.append(action)
            return None
    
    def redo(self) -> Optional[DrawingAction]:
        """Redo the last undone action.
        
        Returns:
            The action that was redone, or None if stack is empty
        """
        if not self.redo_stack:
            return None
        
        action = self.redo_stack.pop()
        try:
            action.redo_func()
            self.undo_stack.append(action)
            return action
        except Exception as e:
            logger.error("Error redoing action: %s", e, exc_info=True)
            # Put action back on stack
            self.redo_stack.append(action)
            return None
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return len(self.redo_stack) > 0
    
    def clear(self) -> None:
        """Clear both undo and redo stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of next action to undo."""
        if not self.undo_stack:
            return None
        action = self.undo_stack[-1]
        return f"Undo {action.action_type}"
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of next action to redo."""
        if not self.redo_stack:
            return None
        action = self.redo_stack[-1]
        return f"Redo {action.action_type}"

