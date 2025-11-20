"""Session template management."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SessionTemplate:
    """Represents a session template."""
    
    def __init__(
        self,
        name: str,
        club: Optional[str] = None,
        session_type: str = "full_swing",
        notes: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ):
        self.name = name
        self.club = club
        self.session_type = session_type
        self.notes = notes
        self.tags = tags or []
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "club": self.club,
            "session_type": self.session_type,
            "notes": self.notes,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionTemplate":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            club=data.get("club"),
            session_type=data.get("session_type", "full_swing"),
            notes=data.get("notes"),
            tags=data.get("tags", []),
        )


class TemplateManager:
    """Manages session templates."""
    
    def __init__(self, templates_file: Path):
        self.templates_file = templates_file
        self.templates: list[SessionTemplate] = []
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load templates from file."""
        if not self.templates_file.exists():
            return
        
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.templates = [SessionTemplate.from_dict(t) for t in data.get("templates", [])]
        except Exception as e:
            logger.error("Error loading templates: %s", e)
            self.templates = []
    
    def _save_templates(self) -> None:
        """Save templates to file."""
        try:
            self.templates_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {"templates": [t.to_dict() for t in self.templates]},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            logger.error("Error saving templates: %s", e)
    
    def add_template(self, template: SessionTemplate) -> None:
        """Add a new template."""
        # Remove existing template with same name
        self.templates = [t for t in self.templates if t.name != template.name]
        self.templates.append(template)
        self._save_templates()
    
    def remove_template(self, name: str) -> None:
        """Remove a template."""
        self.templates = [t for t in self.templates if t.name != name]
        self._save_templates()
    
    def get_template(self, name: str) -> Optional[SessionTemplate]:
        """Get a template by name."""
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def list_templates(self) -> list[SessionTemplate]:
        """List all templates."""
        return self.templates.copy()

