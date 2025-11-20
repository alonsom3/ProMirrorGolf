"""Advanced search functionality for sessions and shots."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Any

from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session

from core.session_manager import SessionModel, ShotModel

logger = logging.getLogger(__name__)


class FilterOperator(Enum):
    """Filter comparison operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    BETWEEN = "between"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"


def search_sessions(
    session: Session,
    query: str,
    include_name: bool = True,
    include_notes: bool = True,
    include_club: bool = True,
    include_tags: bool = True,
) -> list[SessionModel]:
    """Search sessions by text query.
    
    Args:
        session: Database session
        query: Search query string
        include_name: Search in session names
        include_notes: Search in session notes
        include_club: Search in club names
        include_tags: Search in tags
        
    Returns:
        List of matching SessionModel instances
    """
    if not query.strip():
        return []
    
    query_lower = query.lower().strip()
    conditions = []
    
    if include_name:
        conditions.append(SessionModel.name.ilike(f"%{query_lower}%"))
    
    if include_notes:
        conditions.append(SessionModel.notes.ilike(f"%{query_lower}%"))
    
    if include_club:
        conditions.append(SessionModel.club.ilike(f"%{query_lower}%"))
    
    if include_tags:
        # Search in JSON tags array
        conditions.append(SessionModel.tags.ilike(f"%{query_lower}%"))
    
    if not conditions:
        return []
    
    return session.query(SessionModel).filter(or_(*conditions)).all()


def search_shots(
    session: Session,
    query: str,
    include_notes: bool = True,
    include_tags: bool = True,
    include_shot_data: bool = True,
) -> list[ShotModel]:
    """Search shots by text query.
    
    Args:
        session: Database session
        query: Search query string
        include_notes: Search in shot notes
        include_tags: Search in tags
        include_shot_data: Search in shot data fields (as string)
        
    Returns:
        List of matching ShotModel instances
    """
    if not query.strip():
        return []
    
    query_lower = query.lower().strip()
    conditions = []
    
    if include_notes:
        conditions.append(ShotModel.notes.ilike(f"%{query_lower}%"))
    
    if include_tags:
        conditions.append(ShotModel.tags.ilike(f"%{query_lower}%"))
    
    if include_shot_data:
        # Search in numeric fields as strings
        conditions.append(
            or_(
                ShotModel.club_speed.isnot(None) & ShotModel.club_speed.cast(str).ilike(f"%{query_lower}%"),
                ShotModel.ball_speed.isnot(None) & ShotModel.ball_speed.cast(str).ilike(f"%{query_lower}%"),
                ShotModel.spin_rate.isnot(None) & ShotModel.spin_rate.cast(str).ilike(f"%{query_lower}%"),
                ShotModel.carry_distance.isnot(None) & ShotModel.carry_distance.cast(str).ilike(f"%{query_lower}%"),
            )
        )
    
    if not conditions:
        return []
    
    return session.query(ShotModel).filter(or_(*conditions)).all()


def search_all(
    session: Session,
    query: str,
    session_filters: Optional[dict] = None,
    shot_filters: Optional[dict] = None,
) -> tuple[list[SessionModel], list[ShotModel]]:
    """Search both sessions and shots.
    
    Args:
        session: Database session
        query: Search query string
        session_filters: Optional filters for session search
        shot_filters: Optional filters for shot search
        
    Returns:
        Tuple of (matching sessions, matching shots)
    """
    session_filters = session_filters or {}
    shot_filters = shot_filters or {}
    
    sessions = search_sessions(
        session,
        query,
        include_name=session_filters.get("include_name", True),
        include_notes=session_filters.get("include_notes", True),
        include_club=session_filters.get("include_club", True),
        include_tags=session_filters.get("include_tags", True),
    )
    
    shots = search_shots(
        session,
        query,
        include_notes=shot_filters.get("include_notes", True),
        include_tags=shot_filters.get("include_tags", True),
        include_shot_data=shot_filters.get("include_shot_data", True),
    )
    
    return sessions, shots


def apply_advanced_filters(
    session: Session,
    model_class: type[SessionModel | ShotModel],
    criteria: list[dict[str, Any]],
) -> list[SessionModel | ShotModel]:
    """Apply advanced filter criteria to a query.
    
    Args:
        session: Database session
        model_class: Model class (SessionModel or ShotModel)
        criteria: List of filter criteria dicts with keys:
            - field: Field name
            - operator: FilterOperator enum value
            - value: Filter value
            - value2: Second value (for BETWEEN)
            - enabled: Whether criterion is enabled
    
    Returns:
        List of matching model instances
    """
    if not criteria:
        return session.query(model_class).all()
    
    query = session.query(model_class)
    conditions = []
    
    for criterion in criteria:
        if not criterion.get("enabled", True):
            continue
        
        field_name = criterion.get("field")
        operator_str = criterion.get("operator")
        value = criterion.get("value")
        value2 = criterion.get("value2")
        
        if not field_name or not hasattr(model_class, field_name):
            continue
        
        field = getattr(model_class, field_name)
        operator = FilterOperator(operator_str) if operator_str else FilterOperator.EQUALS
        
        condition = None
        
        if operator == FilterOperator.EQUALS:
            condition = field == value
        elif operator == FilterOperator.NOT_EQUALS:
            condition = field != value
        elif operator == FilterOperator.GREATER_THAN:
            condition = field > value
        elif operator == FilterOperator.LESS_THAN:
            condition = field < value
        elif operator == FilterOperator.GREATER_EQUAL:
            condition = field >= value
        elif operator == FilterOperator.LESS_EQUAL:
            condition = field <= value
        elif operator == FilterOperator.BETWEEN:
            if value is not None and value2 is not None:
                condition = field.between(value, value2)
        elif operator == FilterOperator.CONTAINS:
            condition = field.ilike(f"%{value}%")
        elif operator == FilterOperator.NOT_CONTAINS:
            condition = ~field.ilike(f"%{value}%")
        elif operator == FilterOperator.IN:
            if isinstance(value, list):
                condition = field.in_(value)
        elif operator == FilterOperator.NOT_IN:
            if isinstance(value, list):
                condition = ~field.in_(value)
        
        if condition is not None:
            conditions.append(condition)
    
    if conditions:
        query = query.filter(and_(*conditions))
    
    return query.all()


def search_shots_advanced(
    session: Session,
    criteria: list[dict[str, Any]],
    date_range: Optional[tuple[datetime, datetime]] = None,
    session_ids: Optional[list[int]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> tuple[list[ShotModel], int]:
    """Advanced shot search with multiple criteria.
    
    Args:
        session: Database session
        criteria: List of filter criteria
        date_range: Optional date range tuple
        session_ids: Optional list of session IDs to filter by
        limit: Optional result limit
        offset: Optional result offset
    
    Returns:
        Tuple of (matching shots, total count)
    """
    query = session.query(ShotModel)
    
    # Apply date range
    if date_range:
        start_date, end_date = date_range
        query = query.filter(ShotModel.recorded_at >= start_date)
        query = query.filter(ShotModel.recorded_at <= end_date)
    
    # Apply session filter
    if session_ids:
        query = query.filter(ShotModel.session_id.in_(session_ids))
    
    # Apply advanced criteria
    if criteria:
        conditions = []
        for criterion in criteria:
            if not criterion.get("enabled", True):
                continue
            
            field_name = criterion.get("field")
            operator_str = criterion.get("operator")
            value = criterion.get("value")
            value2 = criterion.get("value2")
            
            if not field_name or not hasattr(ShotModel, field_name):
                continue
            
            field = getattr(ShotModel, field_name)
            operator = FilterOperator(operator_str) if operator_str else FilterOperator.EQUALS
            
            condition = None
            
            if operator == FilterOperator.EQUALS:
                condition = field == value
            elif operator == FilterOperator.NOT_EQUALS:
                condition = field != value
            elif operator == FilterOperator.GREATER_THAN:
                condition = field > value
            elif operator == FilterOperator.LESS_THAN:
                condition = field < value
            elif operator == FilterOperator.GREATER_EQUAL:
                condition = field >= value
            elif operator == FilterOperator.LESS_EQUAL:
                condition = field <= value
            elif operator == FilterOperator.BETWEEN:
                if value is not None and value2 is not None:
                    condition = field.between(value, value2)
            elif operator == FilterOperator.CONTAINS:
                condition = field.ilike(f"%{value}%")
            elif operator == FilterOperator.NOT_CONTAINS:
                condition = ~field.ilike(f"%{value}%")
            
            if condition is not None:
                conditions.append(condition)
        
        if conditions:
            query = query.filter(and_(*conditions))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    
    return query.all(), total

