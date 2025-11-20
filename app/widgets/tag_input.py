"""Tag input widget with autocomplete and suggestions."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCompleter,
    QLineEdit,
    QListWidget,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.tag_manager import TagManager

logger = logging.getLogger(__name__)


class TagInputWidget(QWidget):
    """Tag input widget with autocomplete and suggestions."""
    
    tags_changed = pyqtSignal(list)  # Emitted when tags change
    
    def __init__(
        self,
        tag_manager: TagManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.current_tags: list[str] = []
        
        self._build_ui()
        self._setup_autocomplete()
    
    def _build_ui(self) -> None:
        """Build UI."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.XS)
        
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("Enter tags (comma-separated)...")
        from app.design_constants import COLORS, SIZES, SPACING, TYPOGRAPHY
        self.tag_edit.setStyleSheet(f"""

            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {current_colors.ACCENT};
            }}
        """)
        self.tag_edit.textChanged.connect(self._on_text_changed)
        self.tag_edit.returnPressed.connect(self._add_current_tag)
        layout.addWidget(self.tag_edit)
        
        # Suggestions list (initially hidden)
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(150)
        from app.design_constants import COLORS, SIZES, SPACING, TYPOGRAPHY
        self.suggestions_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.SMALL}px;
            }}
            QListWidget::item {{
                padding: 6px {SPACING.MEDIUM}px;
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QListWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
            }}
        """)
        self.suggestions_list.itemDoubleClicked.connect(self._select_suggestion)
        self.suggestions_list.hide()
        layout.addWidget(self.suggestions_list)
    
    def _setup_autocomplete(self) -> None:
        """Set up autocomplete."""
        self.completer = QCompleter([], self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.tag_edit.setCompleter(self.completer)
    
    def _on_text_changed(self, text: str) -> None:
        """Handle text change - update suggestions."""
        if not text.strip():
            self.suggestions_list.hide()
            return
        
        # Get current word being typed
        cursor_pos = self.tag_edit.cursorPosition()
        text_before_cursor = text[:cursor_pos]
        
        # Find the last comma or start of string
        last_comma = text_before_cursor.rfind(",")
        current_word = text_before_cursor[last_comma + 1:].strip()
        
        if current_word:
            suggestions = self.tag_manager.get_tag_suggestions(prefix=current_word, limit=8)
            self._update_suggestions(suggestions)
        else:
            # Show popular tags
            suggestions = self.tag_manager.get_tag_suggestions(limit=8)
            self._update_suggestions(suggestions)
    
    def _update_suggestions(self, suggestions: list[str]) -> None:
        """Update suggestions list."""
        self.suggestions_list.clear()
        
        if not suggestions:
            self.suggestions_list.hide()
            return
        
        for tag in suggestions:
            if tag not in self.current_tags:  # Don't suggest already-added tags
                self.suggestions_list.addItem(tag)
        
        if self.suggestions_list.count() > 0:
            self.suggestions_list.show()
        else:
            self.suggestions_list.hide()
        
        # Update completer
        all_tags = self.tag_manager.get_all_tags()
        self.completer.setModel(None)  # Clear model
        from PyQt6.QtCore import QStringListModel
        self.completer.setModel(QStringListModel(all_tags, self.completer))
    
    def _select_suggestion(self, item) -> None:
        """Select a suggestion from the list."""
        tag = item.text()
        self._add_tag(tag)
        self.tag_edit.clear()
        self.suggestions_list.hide()
    
    def _add_current_tag(self) -> None:
        """Add the current text as a tag."""
        text = self.tag_edit.text().strip()
        if text:
            # Split by comma and add all tags
            tags = [tag.strip() for tag in text.split(",") if tag.strip()]
            for tag in tags:
                self._add_tag(tag)
            self.tag_edit.clear()
            self.suggestions_list.hide()
    
    def _add_tag(self, tag: str) -> None:
        """Add a tag to the list."""
        tag = tag.strip()
        if tag and tag not in self.current_tags:
            self.current_tags.append(tag)
            self.tags_changed.emit(self.current_tags.copy())
    
    def set_tags(self, tags: list[str]) -> None:
        """Set the current tags."""
        self.current_tags = tags.copy()
        self.tags_changed.emit(self.current_tags.copy())
    
    def get_tags(self) -> list[str]:
        """Get current tags."""
        return self.current_tags.copy()
    
    def clear(self) -> None:
        """Clear all tags."""
        self.current_tags.clear()
        self.tag_edit.clear()
        self.suggestions_list.hide()
        self.tags_changed.emit([])

