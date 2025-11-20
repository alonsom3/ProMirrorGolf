"""Quick actions menu for common tasks."""

from __future__ import annotations

from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QMenu, QWidget

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme


class QuickActionsMenu(QMenu):
    """Quick actions menu with common tasks."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Quick Actions", parent)
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        self.setStyleSheet(get_current_theme() + f"""
            QMenu {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                padding: {SPACING.XS}px;
            }}
            QMenu::item {{
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QMenu::item:selected {{
                background-color: {current_colors.ACCENT};
                color: {current_colors.WHITE_TEXT};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {current_colors.BORDER_DEFAULT};
                margin: {SPACING.XS}px {SPACING.SMALL}px;
            }}
        """)
        
        self._build_menu()
    
    def _build_menu(self) -> None:
        """Build the quick actions menu."""
        # Session actions
        self.addAction("Start New Session", lambda: self._trigger_action("start_session"))
        self.addAction("Stop Current Session", lambda: self._trigger_action("stop_session"))
        self.addSeparator()
        
        # Shot actions
        self.addAction("Review Selected Shot", lambda: self._trigger_action("review_shot"))
        self.addAction("Tag Selected Shot", lambda: self._trigger_action("tag_shot"))
        self.addAction("Mark as Favorite", lambda: self._trigger_action("favorite_shot"))
        self.addSeparator()
        
        # Analysis actions
        self.addAction("Open Analysis Dashboard", lambda: self._trigger_action("analysis"))
        self.addAction("Compare Sessions", lambda: self._trigger_action("compare"))
        self.addSeparator()
        
        # Export actions
        self.addAction("Export Selected Shots", lambda: self._trigger_action("export_shots"))
        self.addAction("Export Session Data", lambda: self._trigger_action("export_session"))
        self.addSeparator()
        
        # Utility actions
        self.addAction("Browse Sessions", lambda: self._trigger_action("browse_sessions"))
        self.addAction("Recent Shots", lambda: self._trigger_action("recent_shots"))
        self.addAction("Settings", lambda: self._trigger_action("settings"))
    
    def _trigger_action(self, action: str) -> None:
        """Trigger an action signal."""
        # This will be connected to handlers in the main window
        pass
    
    def set_action_handler(self, action: str, handler: Callable) -> None:
        """Set handler for a specific action."""
        # Find and update the action
        for act in self.actions():
            if act.data() == action:
                act.triggered.disconnect()
                act.triggered.connect(handler)
                break

