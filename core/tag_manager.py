"""Tag management system with categories, suggestions, and autocomplete."""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TagCategory:
    """Represents a tag category."""
    
    def __init__(self, name: str, color: str = "#8b949e", description: str = "") -> None:
        self.name = name
        self.color = color
        self.description = description
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "color": self.color,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> TagCategory:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            color=data.get("color", "#8b949e"),
            description=data.get("description", ""),
        )


class TagManager:
    """Manages tags with categories, suggestions, and autocomplete."""
    
    DEFAULT_CATEGORIES = [
        TagCategory("Club", "#4ade80", "Club type tags"),
        TagCategory("Condition", "#ff4d4d", "Weather/condition tags"),
        TagCategory("Quality", "#ffa500", "Shot quality tags"),
        TagCategory("Technique", "#9d4edd", "Swing technique tags"),
        TagCategory("Custom", "#8b949e", "User-defined tags"),
    ]
    
    def __init__(self, config_file: Path, session_manager) -> None:
        """Initialize tag manager."""
        self.config_file = config_file
        self.session_manager = session_manager
        self.categories: list[TagCategory] = []
        self.tag_to_category: dict[str, str] = {}  # tag -> category_name
        self._load_config()
    
    def _load_config(self) -> None:
        """Load tag configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.categories = [
                    TagCategory.from_dict(cat_data)
                    for cat_data in data.get("categories", [])
                ]
                self.tag_to_category = data.get("tag_to_category", {})
                
                # Ensure default categories exist
                existing_names = {cat.name for cat in self.categories}
                for default_cat in self.DEFAULT_CATEGORIES:
                    if default_cat.name not in existing_names:
                        self.categories.append(default_cat)
                
                logger.info("Loaded tag configuration from %s", self.config_file)
            except Exception as e:
                logger.warning("Failed to load tag config: %s, using defaults", e)
                self.categories = self.DEFAULT_CATEGORIES.copy()
                self.tag_to_category = {}
        else:
            self.categories = self.DEFAULT_CATEGORIES.copy()
            self.tag_to_category = {}
            self._save_config()
    
    def _save_config(self) -> None:
        """Save tag configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "categories": [cat.to_dict() for cat in self.categories],
                "tag_to_category": self.tag_to_category,
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved tag configuration to %s", self.config_file)
        except Exception as e:
            logger.error("Failed to save tag config: %s", e, exc_info=True)
    
    def get_all_tags(self) -> list[str]:
        """Get all unique tags from database."""
        try:
            with Session(self.session_manager.engine) as session:
                # Get tags from shots
                shots_result = session.execute(text("SELECT tags FROM shots WHERE tags IS NOT NULL"))
                shot_tags = []
                for row in shots_result:
                    if row[0]:
                        try:
                            shot_tags.extend(json.loads(row[0]))
                        except:
                            pass
                
                # Get tags from sessions
                sessions_result = session.execute(text("SELECT tags FROM sessions WHERE tags IS NOT NULL"))
                session_tags = []
                for row in sessions_result:
                    if row[0]:
                        try:
                            session_tags.extend(json.loads(row[0]))
                        except:
                            pass
                
                all_tags = list(set(shot_tags + session_tags))
                return sorted(all_tags)
        except Exception as e:
            logger.error("Error getting all tags: %s", e, exc_info=True)
            return []
    
    def get_tag_suggestions(self, prefix: str = "", limit: int = 10) -> list[str]:
        """Get tag suggestions based on prefix and frequency."""
        all_tags = self.get_all_tags()
        
        if prefix:
            matching = [tag for tag in all_tags if tag.lower().startswith(prefix.lower())]
        else:
            matching = all_tags
        
        # Get frequency counts
        try:
            with Session(self.session_manager.engine) as session:
                # Count tag usage in shots
                shots_result = session.execute(text("SELECT tags FROM shots WHERE tags IS NOT NULL"))
                tag_counts = Counter()
                for row in shots_result:
                    if row[0]:
                        try:
                            tags = json.loads(row[0])
                            tag_counts.update(tags)
                        except:
                            pass
                
                # Count tag usage in sessions
                sessions_result = session.execute(text("SELECT tags FROM sessions WHERE tags IS NOT NULL"))
                for row in sessions_result:
                    if row[0]:
                        try:
                            tags = json.loads(row[0])
                            tag_counts.update(tags)
                        except:
                            pass
                
                # Sort by frequency, then alphabetically
                matching_with_counts = [
                    (tag, tag_counts.get(tag, 0))
                    for tag in matching
                ]
                matching_with_counts.sort(key=lambda x: (-x[1], x[0]))
                
                return [tag for tag, _ in matching_with_counts[:limit]]
        except Exception as e:
            logger.error("Error getting tag suggestions: %s", e, exc_info=True)
            return matching[:limit]
    
    def get_category_for_tag(self, tag: str) -> Optional[str]:
        """Get category name for a tag."""
        return self.tag_to_category.get(tag)
    
    def set_tag_category(self, tag: str, category_name: str) -> None:
        """Assign a tag to a category."""
        self.tag_to_category[tag] = category_name
        self._save_config()
    
    def get_categories(self) -> list[TagCategory]:
        """Get all categories."""
        return self.categories.copy()
    
    def add_category(self, category: TagCategory) -> None:
        """Add a new category."""
        if not any(cat.name == category.name for cat in self.categories):
            self.categories.append(category)
            self._save_config()
    
    def remove_category(self, category_name: str) -> None:
        """Remove a category."""
        self.categories = [cat for cat in self.categories if cat.name != category_name]
        # Remove category assignments
        self.tag_to_category = {
            tag: cat for tag, cat in self.tag_to_category.items()
            if cat != category_name
        }
        self._save_config()
    
    def update_category(self, category_name: str, **kwargs) -> None:
        """Update category properties."""
        for cat in self.categories:
            if cat.name == category_name:
                if "color" in kwargs:
                    cat.color = kwargs["color"]
                if "description" in kwargs:
                    cat.description = kwargs["description"]
                self._save_config()
                return

