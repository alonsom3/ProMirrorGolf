"""Practice drills and exercises management."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Drill:
    """A practice drill or exercise."""
    name: str
    description: str
    category: str  # "tempo", "path", "impact", "consistency", etc.
    instructions: list[str]
    target_metrics: dict  # Target values for metrics
    duration_minutes: int = 10
    difficulty: str = "intermediate"  # "beginner", "intermediate", "advanced"
    video_example_path: Optional[str] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class DrillSession:
    """A completed drill session."""
    drill_name: str
    session_id: Optional[int] = None
    started_at: str = ""
    completed_at: Optional[str] = None
    shots_taken: int = 0
    target_achieved: bool = False
    notes: str = ""
    
    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()


class PracticeDrillManager:
    """Manages practice drills and tracks drill sessions."""
    
    DEFAULT_DRILLS = [
        Drill(
            name="Tempo Training",
            description="Practice maintaining consistent tempo ratio",
            category="tempo",
            instructions=[
                "Focus on maintaining a 3:1 backswing to downswing ratio",
                "Take 10 swings focusing only on tempo",
                "Review tempo ratio after each swing",
                "Aim for consistency within 0.1 of target ratio"
            ],
            target_metrics={"tempo_ratio": 3.0, "consistency": 0.1},
            duration_minutes=15,
            difficulty="beginner"
        ),
        Drill(
            name="Swing Path Correction",
            description="Work on improving swing path",
            category="path",
            instructions=[
                "Set up alignment sticks or reference lines",
                "Take 20 swings focusing on path",
                "Review path visualization after each swing",
                "Identify and correct path deviations"
            ],
            target_metrics={"path_deviation": 5.0},  # degrees
            duration_minutes=20,
            difficulty="intermediate"
        ),
        Drill(
            name="Impact Position Practice",
            description="Focus on impact position and ball contact",
            category="impact",
            instructions=[
                "Use slow motion playback to analyze impact",
                "Take 15 swings focusing on impact position",
                "Review impact frame for each swing",
                "Adjust setup and swing to improve impact"
            ],
            target_metrics={"impact_consistency": 0.8},
            duration_minutes=15,
            difficulty="intermediate"
        ),
        Drill(
            name="Distance Consistency",
            description="Improve distance consistency",
            category="consistency",
            instructions=[
                "Hit 20 shots with the same club",
                "Focus on consistent carry distance",
                "Review dispersion pattern",
                "Aim for standard deviation under 10 yards"
            ],
            target_metrics={"carry_std": 10.0, "shots": 20},
            duration_minutes=25,
            difficulty="advanced"
        ),
    ]
    
    def __init__(self, drills_file: Path, sessions_file: Path) -> None:
        """Initialize practice drill manager.
        
        Args:
            drills_file: Path to JSON file storing drills
            sessions_file: Path to JSON file storing drill sessions
        """
        self.drills_file = drills_file
        self.sessions_file = sessions_file
        self.drills: list[Drill] = []
        self.drill_sessions: list[DrillSession] = []
        self._load_drills()
        self._load_sessions()
    
    def _load_drills(self) -> None:
        """Load drills from file."""
        if not self.drills_file.exists():
            # Use defaults
            self.drills = self.DEFAULT_DRILLS.copy()
            self._save_drills()
            return
        
        try:
            with open(self.drills_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.drills = [Drill(**d) for d in data.get("drills", [])]
            
            if not self.drills:
                self.drills = self.DEFAULT_DRILLS.copy()
                self._save_drills()
        except Exception as e:
            logger.error("Error loading drills: %s", e, exc_info=True)
            self.drills = self.DEFAULT_DRILLS.copy()
    
    def _save_drills(self) -> None:
        """Save drills to file."""
        try:
            self.drills_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.drills_file, 'w', encoding='utf-8') as f:
                json.dump({"drills": [asdict(d) for d in self.drills]}, f, indent=2)
        except Exception as e:
            logger.error("Error saving drills: %s", e, exc_info=True)
    
    def _load_sessions(self) -> None:
        """Load drill sessions from file."""
        if not self.sessions_file.exists():
            return
        
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.drill_sessions = [DrillSession(**s) for s in data.get("sessions", [])]
        except Exception as e:
            logger.error("Error loading drill sessions: %s", e, exc_info=True)
            self.drill_sessions = []
    
    def _save_sessions(self) -> None:
        """Save drill sessions to file."""
        try:
            self.sessions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump({"sessions": [asdict(s) for s in self.drill_sessions]}, f, indent=2)
        except Exception as e:
            logger.error("Error saving drill sessions: %s", e, exc_info=True)
    
    def add_drill(self, drill: Drill) -> None:
        """Add a new drill."""
        self.drills.append(drill)
        self._save_drills()
    
    def get_drill(self, name: str) -> Optional[Drill]:
        """Get a drill by name."""
        for drill in self.drills:
            if drill.name == name:
                return drill
        return None
    
    def get_drills_by_category(self, category: str) -> list[Drill]:
        """Get all drills in a category."""
        return [d for d in self.drills if d.category == category]
    
    def get_all_drills(self) -> list[Drill]:
        """Get all drills."""
        return self.drills.copy()
    
    def start_drill_session(self, drill_name: str, session_id: Optional[int] = None) -> DrillSession:
        """Start a new drill session.
        
        Args:
            drill_name: Name of drill
            session_id: Optional session ID to link to
            
        Returns:
            Created drill session
        """
        session = DrillSession(drill_name=drill_name, session_id=session_id)
        self.drill_sessions.append(session)
        self._save_sessions()
        return session
    
    def complete_drill_session(self, session: DrillSession, shots_taken: int, 
                             target_achieved: bool, notes: str = "") -> None:
        """Complete a drill session.
        
        Args:
            session: Drill session to complete
            shots_taken: Number of shots taken
            target_achieved: Whether target was achieved
            notes: Optional notes
        """
        session.completed_at = datetime.now().isoformat()
        session.shots_taken = shots_taken
        session.target_achieved = target_achieved
        session.notes = notes
        self._save_sessions()
    
    def get_drill_history(self, drill_name: str) -> list[DrillSession]:
        """Get history of drill sessions for a specific drill."""
        return [s for s in self.drill_sessions if s.drill_name == drill_name]

