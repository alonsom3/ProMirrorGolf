"""Auto-tagging system based on shot criteria."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TaggingRule:
    """A rule for auto-tagging shots."""
    name: str
    description: str
    field: str
    operator: str  # ">", "<", ">=", "<=", "==", "between"
    value: float
    tag: str
    value2: Optional[float] = None  # For "between" operator
    enabled: bool = True


class AutoTaggingManager:
    """Manages auto-tagging rules and applies them to shots."""
    
    DEFAULT_RULES = [
        TaggingRule(
            name="Long Carry",
            description="Tag shots with carry distance > 250 yards",
            field="carry_distance",
            operator=">",
            value=250.0,
            tag="long",
            enabled=True,
        ),
        TaggingRule(
            name="High Speed",
            description="Tag shots with club speed > 100 mph",
            field="club_speed",
            operator=">",
            value=100.0,
            tag="high-speed",
            enabled=True,
        ),
        TaggingRule(
            name="Good Smash Factor",
            description="Tag shots with smash factor > 1.45",
            field="smash_factor",
            operator=">",
            value=1.45,
            tag="good-contact",
            enabled=True,
        ),
        TaggingRule(
            name="Consistent Distance",
            description="Tag shots with carry between 200-250 yards",
            field="carry_distance",
            operator="between",
            value=200.0,
            value2=250.0,
            tag="consistent",
            enabled=True,
        ),
    ]
    
    def __init__(self) -> None:
        """Initialize auto-tagging manager."""
        self.rules: list[TaggingRule] = self.DEFAULT_RULES.copy()
    
    def apply_rules(self, shot) -> list[str]:
        """Apply all enabled rules to a shot and return tags to add.
        
        Args:
            shot: ShotModel instance
            
        Returns:
            List of tags to add
        """
        tags_to_add = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            field_value = getattr(shot, rule.field, None)
            if field_value is None:
                continue
            
            should_tag = False
            
            if rule.operator == ">":
                should_tag = field_value > rule.value
            elif rule.operator == "<":
                should_tag = field_value < rule.value
            elif rule.operator == ">=":
                should_tag = field_value >= rule.value
            elif rule.operator == "<=":
                should_tag = field_value <= rule.value
            elif rule.operator == "==":
                should_tag = abs(field_value - rule.value) < 0.01
            elif rule.operator == "between":
                if rule.value2 is not None:
                    should_tag = rule.value <= field_value <= rule.value2
            
            if should_tag:
                tags_to_add.append(rule.tag)
        
        return tags_to_add
    
    def add_rule(self, rule: TaggingRule) -> None:
        """Add a new tagging rule."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False
    
    def get_rules(self) -> list[TaggingRule]:
        """Get all rules."""
        return self.rules.copy()

