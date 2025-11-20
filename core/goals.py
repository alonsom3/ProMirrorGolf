"""Goal setting and tracking functionality."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import Session

from core.session_manager import Base

logger = logging.getLogger(__name__)


class GoalModel(Base):
    """Goal model for tracking performance targets."""
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    metric = Column(String, nullable=False)  # e.g., "club_speed", "ball_speed", "carry_distance"
    target_value = Column(Float, nullable=False)
    operator = Column(String, nullable=False)  # ">=", "<=", "=="
    club_type = Column(String, nullable=True)  # Optional club filter
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    notes = Column(String, nullable=True)


def create_goal_table(engine):
    """Create goals table if it doesn't exist."""
    Base.metadata.create_all(engine)


def add_goal(
    session: Session,
    name: str,
    metric: str,
    target_value: float,
    operator: str = ">=",
    club_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    notes: Optional[str] = None,
) -> GoalModel:
    """Add a new goal.
    
    Args:
        session: Database session
        name: Goal name
        metric: Metric to track (e.g., "club_speed")
        target_value: Target value
        operator: Comparison operator (">=", "<=", "==")
        club_type: Optional club type filter
        start_date: Optional start date
        end_date: Optional end date
        notes: Optional notes
        
    Returns:
        Created GoalModel instance
    """
    goal = GoalModel(
        name=name,
        metric=metric,
        target_value=target_value,
        operator=operator,
        club_type=club_type,
        start_date=start_date,
        end_date=end_date,
        notes=notes,
        is_active=True,
    )
    session.add(goal)
    session.commit()
    logger.info("Created goal: %s (metric: %s, target: %s %s)", name, metric, operator, target_value)
    return goal


def get_goals(session: Session, active_only: bool = True) -> list[GoalModel]:
    """Get all goals.
    
    Args:
        session: Database session
        active_only: Only return active goals
        
    Returns:
        List of GoalModel instances
    """
    query = session.query(GoalModel)
    if active_only:
        query = query.filter(GoalModel.is_active == True)
    return query.all()


def check_goal_progress(
    session: Session,
    goal: GoalModel,
    shots: list,
) -> dict:
    """Check progress toward a goal.
    
    Args:
        session: Database session
        goal: Goal to check
        shots: List of shots to evaluate
        
    Returns:
        Dictionary with progress information
    """
    if not shots:
        return {
            "total_shots": 0,
            "achieved": 0,
            "percentage": 0.0,
            "average": None,
            "best": None,
        }
    
    # Filter by club type if specified
    if goal.club_type:
        shots = [s for s in shots if s.club_speed and getattr(s, 'club', None) == goal.club_type]
    
    # Filter by date range if specified
    if goal.start_date:
        shots = [s for s in shots if s.recorded_at >= goal.start_date]
    if goal.end_date:
        shots = [s for s in shots if s.recorded_at <= goal.end_date]
    
    # Get metric values
    metric_values = []
    for shot in shots:
        value = getattr(shot, goal.metric, None)
        if value is not None:
            metric_values.append(float(value))
    
    if not metric_values:
        return {
            "total_shots": len(shots),
            "achieved": 0,
            "percentage": 0.0,
            "average": None,
            "best": None,
        }
    
    # Check achievement
    achieved = 0
    if goal.operator == ">=":
        achieved = sum(1 for v in metric_values if v >= goal.target_value)
    elif goal.operator == "<=":
        achieved = sum(1 for v in metric_values if v <= goal.target_value)
    elif goal.operator == "==":
        achieved = sum(1 for v in metric_values if abs(v - goal.target_value) < 0.1)
    
    return {
        "total_shots": len(shots),
        "achieved": achieved,
        "percentage": (achieved / len(shots)) * 100.0 if shots else 0.0,
        "average": sum(metric_values) / len(metric_values) if metric_values else None,
        "best": max(metric_values) if metric_values else None,
    }

