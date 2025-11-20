"""Session notes templates for common session types."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NotesTemplate:
    """A template for session notes."""
    name: str
    description: str
    content: str
    category: str = "general"
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            from datetime import datetime
            self.created_at = datetime.now().isoformat()


class NotesTemplateManager:
    """Manages session notes templates."""
    
    DEFAULT_TEMPLATES = [
        NotesTemplate(
            name="Practice Session",
            description="Standard practice session notes",
            content="Practice Session Notes:\n\nFocus Areas:\n- \n- \n\nObservations:\n- \n- \n\nNext Steps:\n- ",
            category="practice",
        ),
        NotesTemplate(
            name="Lesson Session",
            description="Notes for a lesson with instructor",
            content="Lesson Session Notes:\n\nInstructor: \nDate: \n\nKey Points:\n- \n- \n\nDrills:\n- \n- \n\nHomework:\n- ",
            category="lesson",
        ),
        NotesTemplate(
            name="Range Session",
            description="Range practice session",
            content="Range Session Notes:\n\nClub: \nConditions: \n\nFocus:\n- \n\nResults:\n- ",
            category="range",
        ),
        NotesTemplate(
            name="Course Play",
            description="On-course playing session",
            content="Course Play Notes:\n\nCourse: \nConditions: \n\nHighlights:\n- \n\nAreas to Work On:\n- ",
            category="course",
        ),
    ]
    
    def __init__(self, templates_file: Path) -> None:
        """Initialize notes template manager.
        
        Args:
            templates_file: Path to JSON file storing templates
        """
        self.templates_file = templates_file
        self.templates: list[NotesTemplate] = []
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load templates from file."""
        if not self.templates_file.exists():
            # Use defaults
            self.templates = self.DEFAULT_TEMPLATES.copy()
            self._save_templates()
            return
        
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.templates = [NotesTemplate(**t) for t in data.get("templates", [])]
            
            # Add defaults if file is empty
            if not self.templates:
                self.templates = self.DEFAULT_TEMPLATES.copy()
                self._save_templates()
        except Exception as e:
            logger.error("Error loading notes templates: %s", e, exc_info=True)
            self.templates = self.DEFAULT_TEMPLATES.copy()
    
    def _save_templates(self) -> None:
        """Save templates to file."""
        try:
            self.templates_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump({"templates": [asdict(t) for t in self.templates]}, f, indent=2)
        except Exception as e:
            logger.error("Error saving notes templates: %s", e, exc_info=True)
    
    def add_template(self, template: NotesTemplate) -> None:
        """Add a new template."""
        self.templates.append(template)
        self._save_templates()
    
    def remove_template(self, name: str) -> bool:
        """Remove a template by name."""
        for i, template in enumerate(self.templates):
            if template.name == name:
                self.templates.pop(i)
                self._save_templates()
                return True
        return False
    
    def get_template(self, name: str) -> Optional[NotesTemplate]:
        """Get a template by name."""
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def get_templates_by_category(self, category: str) -> list[NotesTemplate]:
        """Get all templates in a category."""
        return [t for t in self.templates if t.category == category]
    
    def get_all_templates(self) -> list[NotesTemplate]:
        """Get all templates."""
        return self.templates.copy()

