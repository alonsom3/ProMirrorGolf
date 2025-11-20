"""Custom fields management system for user-defined data fields."""

from __future__ import annotations

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    """Supported field types."""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    SELECT = "select"  # Dropdown with predefined options


class CustomField:
    """Represents a custom field definition."""
    
    def __init__(
        self,
        name: str,
        field_type: FieldType,
        label: str,
        description: str = "",
        default_value: Any = None,
        required: bool = False,
        options: Optional[list[str]] = None,  # For SELECT type
        applies_to: str = "shots",  # "shots" or "sessions"
    ) -> None:
        self.name = name  # Internal field name (no spaces, lowercase)
        self.field_type = field_type
        self.label = label  # Display label
        self.description = description
        self.default_value = default_value
        self.required = required
        self.options = options or []  # For SELECT type
        self.applies_to = applies_to  # "shots" or "sessions"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "field_type": self.field_type.value,
            "label": self.label,
            "description": self.description,
            "default_value": self.default_value,
            "required": self.required,
            "options": self.options,
            "applies_to": self.applies_to,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> CustomField:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            field_type=FieldType(data["field_type"]),
            label=data.get("label", data["name"]),
            description=data.get("description", ""),
            default_value=data.get("default_value"),
            required=data.get("required", False),
            options=data.get("options", []),
            applies_to=data.get("applies_to", "shots"),
        )
    
    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a value for this field. Returns (is_valid, error_message)."""
        if value is None or value == "":
            if self.required:
                return False, f"{self.label} is required"
            return True, None
        
        if self.field_type == FieldType.NUMBER:
            try:
                float(value)
            except (ValueError, TypeError):
                return False, f"{self.label} must be a number"
        
        if self.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"{self.label} must be true or false"
        
        if self.field_type == FieldType.SELECT:
            if value not in self.options:
                return False, f"{self.label} must be one of: {', '.join(self.options)}"
        
        return True, None


class CustomFieldManager:
    """Manages custom field definitions."""
    
    def __init__(self, config_file: Path) -> None:
        """Initialize custom field manager."""
        self.config_file = config_file
        self.fields: list[CustomField] = []
        self._load_config()
    
    def _load_config(self) -> None:
        """Load custom field definitions from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.fields = [
                    CustomField.from_dict(field_data)
                    for field_data in data.get("fields", [])
                ]
                
                logger.info("Loaded %d custom fields from %s", len(self.fields), self.config_file)
            except Exception as e:
                logger.warning("Failed to load custom fields config: %s, using defaults", e)
                self.fields = []
        else:
            self.fields = []
            self._save_config()
    
    def _save_config(self) -> None:
        """Save custom field definitions to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "fields": [field.to_dict() for field in self.fields],
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved custom fields config to %s", self.config_file)
        except Exception as e:
            logger.error("Failed to save custom fields config: %s", e, exc_info=True)
    
    def add_field(self, field: CustomField) -> bool:
        """Add a new custom field."""
        # Check for duplicate names
        if any(f.name == field.name for f in self.fields):
            logger.warning("Field with name '%s' already exists", field.name)
            return False
        
        self.fields.append(field)
        self._save_config()
        return True
    
    def remove_field(self, field_name: str) -> bool:
        """Remove a custom field."""
        original_count = len(self.fields)
        self.fields = [f for f in self.fields if f.name != field_name]
        
        if len(self.fields) < original_count:
            self._save_config()
            return True
        return False
    
    def update_field(self, field_name: str, **kwargs) -> bool:
        """Update a custom field."""
        for field in self.fields:
            if field.name == field_name:
                for key, value in kwargs.items():
                    if hasattr(field, key):
                        setattr(field, key, value)
                self._save_config()
                return True
        return False
    
    def get_field(self, field_name: str) -> Optional[CustomField]:
        """Get a field by name."""
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
    
    def get_fields_for(self, applies_to: str) -> list[CustomField]:
        """Get all fields that apply to shots or sessions."""
        return [f for f in self.fields if f.applies_to == applies_to]
    
    def get_all_fields(self) -> list[CustomField]:
        """Get all custom fields."""
        return self.fields.copy()
    
    def validate_custom_fields(self, applies_to: str, custom_fields: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate custom field values. Returns (is_valid, error_message)."""
        fields_for_type = self.get_fields_for(applies_to)
        
        for field in fields_for_type:
            value = custom_fields.get(field.name)
            is_valid, error_msg = field.validate_value(value)
            if not is_valid:
                return False, error_msg
        
        return True, None


def get_custom_fields_from_json(json_str: Optional[str]) -> dict[str, Any]:
    """Parse custom fields from JSON string."""
    if not json_str:
        return {}
    try:
        return json.loads(json_str)
    except:
        return {}


def set_custom_fields_to_json(custom_fields: dict[str, Any]) -> Optional[str]:
    """Convert custom fields dict to JSON string."""
    if not custom_fields:
        return None
    return json.dumps(custom_fields)

