"""Undo/redo system for shot edits."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class EditAction:
    """Represents an edit action that can be undone/redone."""
    action_type: str
    shot_id: int
    field: str
    old_value: Any
    new_value: Any
    undo_func: Callable
    redo_func: Callable


class UndoRedoManager:
    """Manages undo/redo stack for shot edits."""
    
    def __init__(self, max_stack_size: int = 50) -> None:
        """Initialize undo/redo manager.
        
        Args:
            max_stack_size: Maximum number of actions to keep in stack
        """
        self.undo_stack: list[EditAction] = []
        self.redo_stack: list[EditAction] = []
        self.max_stack_size = max_stack_size
    
    def push_action(self, action: EditAction) -> None:
        """Push an action onto the undo stack.
        
        Args:
            action: The edit action to push
        """
        self.undo_stack.append(action)
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new action is pushed
        self.redo_stack.clear()
        
        logger.debug("Pushed action: %s on shot %d", action.action_type, action.shot_id)
    
    def undo(self) -> Optional[EditAction]:
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
            logger.debug("Undid action: %s on shot %d", action.action_type, action.shot_id)
            return action
        except Exception as e:
            logger.error("Error undoing action: %s", e, exc_info=True)
            # Put action back on stack
            self.undo_stack.append(action)
            return None
    
    def redo(self) -> Optional[EditAction]:
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
            logger.debug("Redid action: %s on shot %d", action.action_type, action.shot_id)
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
        logger.debug("Cleared undo/redo stacks")
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of next action to undo."""
        if not self.undo_stack:
            return None
        action = self.undo_stack[-1]
        return f"Undo {action.action_type}: {action.field}"
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of next action to redo."""
        if not self.redo_stack:
            return None
        action = self.redo_stack[-1]
        return f"Redo {action.action_type}: {action.field}"

