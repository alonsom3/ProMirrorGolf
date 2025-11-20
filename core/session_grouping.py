"""Smart session grouping based on criteria."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionGroup:
    """A group of related sessions."""
    name: str
    description: str
    session_ids: list[int]
    criteria: dict
    created_at: datetime


class SessionGroupingManager:
    """Manages smart grouping of sessions."""
    
    def __init__(self) -> None:
        """Initialize session grouping manager."""
        self.groups: list[SessionGroup] = []
    
    def group_by_club(self, sessions: list) -> dict[str, list[int]]:
        """Group sessions by club.
        
        Args:
            sessions: List of SessionModel instances
            
        Returns:
            Dictionary mapping club names to session IDs
        """
        groups = {}
        for session in sessions:
            club = session.club or "Unknown"
            if club not in groups:
                groups[club] = []
            groups[club].append(session.id)
        return groups
    
    def group_by_date_range(self, sessions: list, days: int = 7) -> dict[str, list[int]]:
        """Group sessions by date range.
        
        Args:
            sessions: List of SessionModel instances
            days: Number of days per group
            
        Returns:
            Dictionary mapping date range strings to session IDs
        """
        groups = {}
        for session in sessions:
            date_key = session.started_at.strftime("%Y-%m-%d")
            week_start = session.started_at - timedelta(days=session.started_at.weekday())
            week_key = f"Week of {week_start.strftime('%Y-%m-%d')}"
            
            if week_key not in groups:
                groups[week_key] = []
            groups[week_key].append(session.id)
        return groups
    
    def group_by_performance(self, sessions: list, threshold: float = 250.0) -> dict[str, list[int]]:
        """Group sessions by average carry distance.
        
        Args:
            sessions: List of SessionModel instances
            threshold: Threshold for "good" performance
            
        Returns:
            Dictionary mapping performance categories to session IDs
        """
        groups = {"Above Average": [], "Below Average": []}
        
        for session in sessions:
            if hasattr(session, 'shots') and session.shots:
                avg_carry = sum(s.carry_distance for s in session.shots if s.carry_distance) / len([s for s in session.shots if s.carry_distance])
                if avg_carry >= threshold:
                    groups["Above Average"].append(session.id)
                else:
                    groups["Below Average"].append(session.id)
        
        return groups
    
    def create_custom_group(self, name: str, description: str, session_ids: list[int], criteria: dict) -> SessionGroup:
        """Create a custom session group.
        
        Args:
            name: Group name
            description: Group description
            session_ids: List of session IDs in group
            criteria: Criteria used to create group
            
        Returns:
            Created SessionGroup
        """
        group = SessionGroup(
            name=name,
            description=description,
            session_ids=session_ids,
            criteria=criteria,
            created_at=datetime.now(),
        )
        self.groups.append(group)
        return group
    
    def get_groups(self) -> list[SessionGroup]:
        """Get all groups."""
        return self.groups.copy()

