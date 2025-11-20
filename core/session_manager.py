from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Boolean,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    metadata = MetaData()


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String)
    club: Mapped[Optional[str]] = mapped_column(String)
    session_type: Mapped[Optional[str]] = mapped_column(String, default="full_swing")  # "full_swing" or "putting" (extensible)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    ended_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)
    tags: Mapped[Optional[str]] = mapped_column(String)  # JSON array of tags
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_fields: Mapped[Optional[str]] = mapped_column(String)  # JSON object for custom field values

    shots: Mapped[list["ShotModel"]] = relationship("ShotModel", back_populates="session")


class ShotModel(Base):
    __tablename__ = "shots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    recorded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    
    # Core metrics
    club_speed: Mapped[Optional[float]] = mapped_column(Float)
    ball_speed: Mapped[Optional[float]] = mapped_column(Float)
    launch_angle: Mapped[Optional[float]] = mapped_column(Float)
    spin_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    # Distance metrics
    carry_distance: Mapped[Optional[float]] = mapped_column(Float)
    total_distance: Mapped[Optional[float]] = mapped_column(Float)
    
    # Spin breakdown
    side_spin: Mapped[Optional[float]] = mapped_column(Float)
    back_spin: Mapped[Optional[float]] = mapped_column(Float)
    
    # Launch metrics
    launch_direction: Mapped[Optional[float]] = mapped_column(Float)  # Degrees left/right
    apex_height: Mapped[Optional[float]] = mapped_column(Float)
    descent_angle: Mapped[Optional[float]] = mapped_column(Float)
    
    # Club metrics
    smash_factor: Mapped[Optional[float]] = mapped_column(Float)
    dynamic_loft: Mapped[Optional[float]] = mapped_column(Float)
    attack_angle: Mapped[Optional[float]] = mapped_column(Float)
    club_path: Mapped[Optional[float]] = mapped_column(Float)
    face_angle: Mapped[Optional[float]] = mapped_column(Float)
    
    # Video paths (extensible - can add putting_video_path later)
    dtl_video_path: Mapped[Optional[str]] = mapped_column(String)
    face_video_path: Mapped[Optional[str]] = mapped_column(String)
    putting_video_path: Mapped[Optional[str]] = mapped_column(String)  # For future putting integration
    
    # Metadata
    raw_json: Mapped[str] = mapped_column(String)
    tags: Mapped[Optional[str]] = mapped_column(String)  # JSON array of tags
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String)
    custom_fields: Mapped[Optional[str]] = mapped_column(String)  # JSON object for custom field values

    session: Mapped[SessionModel] = relationship("SessionModel", back_populates="shots")


class SessionManager:
    """SQLite-backed session/shot persistence."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # SQLite connection with check_same_thread=False for multi-threaded access
        # and timeout=20 seconds to handle concurrent access better
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            future=True,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False, "timeout": 20}
        )
        Base.metadata.create_all(self.engine)
        self._migrate_database()
        self._active_session_id: Optional[int] = None

    def _migrate_database(self) -> None:
        """Migrate database schema if needed."""
        import sqlite3
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create indexes for performance optimization
            indexes = [
                ("idx_shots_session_id", "shots", "session_id"),
                ("idx_shots_recorded_at", "shots", "recorded_at"),
                ("idx_shots_carry_distance", "shots", "carry_distance"),
                ("idx_shots_club_speed", "shots", "club_speed"),
                ("idx_shots_ball_speed", "shots", "ball_speed"),
                ("idx_shots_is_favorite", "shots", "is_favorite"),
                ("idx_sessions_started_at", "sessions", "started_at"),
                ("idx_sessions_club", "sessions", "club"),
                ("idx_sessions_is_favorite", "sessions", "is_favorite"),
            ]
            
            for index_name, table, column in indexes:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                except Exception as e:
                    logger.debug("Index %s may already exist: %s", index_name, e)
            
            # Check shots table columns
            cursor.execute("PRAGMA table_info(shots)")
            shot_columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns to shots table
            new_shot_columns = {
                "dtl_video_path": "TEXT",
                "face_video_path": "TEXT",
                "putting_video_path": "TEXT",  # For future putting integration
                "carry_distance": "REAL",
                "total_distance": "REAL",
                "side_spin": "REAL",
                "back_spin": "REAL",
                "launch_direction": "REAL",
                "apex_height": "REAL",
                "descent_angle": "REAL",
                "smash_factor": "REAL",
                "dynamic_loft": "REAL",
                "attack_angle": "REAL",
                "club_path": "REAL",
                "face_angle": "REAL",
                "tags": "TEXT",
                "is_favorite": "INTEGER DEFAULT 0",
                "notes": "TEXT",
                "custom_fields": "TEXT",  # JSON object for custom field values
            }
            
            for col_name, col_type in new_shot_columns.items():
                if col_name not in shot_columns:
                    logger.debug("Adding %s column to shots table", col_name)
                    cursor.execute(f"ALTER TABLE shots ADD COLUMN {col_name} {col_type}")
            
            # Check sessions table columns
            cursor.execute("PRAGMA table_info(sessions)")
            session_columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns to sessions table
            new_session_columns = {
                "notes": "TEXT",
                "club": "TEXT",
                "session_type": "TEXT DEFAULT 'full_swing'",
                "tags": "TEXT",
                "is_favorite": "INTEGER DEFAULT 0",
                "custom_fields": "TEXT",  # JSON object for custom field values
            }
            
            for col_name, col_type in new_session_columns.items():
                if col_name not in session_columns:
                    logger.debug("Adding %s column to sessions table", col_name)
                    cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col_name} {col_type}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Database migration error (may be expected on first run): %s", e)

    def start_session(
        self,
        name: str,
        session_type: str = "full_swing",
        club: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> int:
        """Start a new session. session_type can be 'full_swing' or 'putting' (extensible)."""
        with Session(self.engine) as session, session.begin():
            record = SessionModel(name=name, session_type=session_type)
            if club:
                record.club = club
            if notes:
                record.notes = notes
            if tags:
                record.tags = json.dumps(tags)
            session.add(record)
            session.flush()
            self._active_session_id = record.id
            logger.info("Session started (%s, type=%s, club=%s)", name, session_type, club)
            return record.id

    def end_session(self) -> None:
        if self._active_session_id is None:
            return
        
        session_id = self._active_session_id
        with Session(self.engine) as session, session.begin():
            record = session.get(SessionModel, session_id)
            if record:
                record.ended_at = dt.datetime.utcnow()
        self._active_session_id = None
        logger.info("Session ended (%s)", session_id)

    def log_shot(self, payload: dict, dtl_video_path: Optional[str] = None, face_video_path: Optional[str] = None, putting_video_path: Optional[str] = None) -> int:
        """Log a shot and return the shot ID.
        
        Thread-safe database write with retry logic for concurrent access.
        """
        if self._active_session_id is None:
            logger.debug("No active session; shot discarded.")
            return -1

        raw_json_str = json.dumps(payload) if isinstance(payload, dict) else str(payload)
        
        # Helper to get value with fallback keys
        def get_val(*keys):
            for key in keys:
                val = payload.get(key)
                if val is not None:
                    return val
            return None

        # Retry logic for database concurrency (SQLite can lock under heavy load)
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                with Session(self.engine) as session, session.begin():
                    shot = ShotModel(
                        session_id=self._active_session_id,
                        club_speed=get_val("ClubSpeed", "club_speed"),
                        ball_speed=get_val("BallSpeed", "ball_speed"),
                        launch_angle=get_val("LaunchAngle", "launch_angle"),
                        spin_rate=get_val("TotalSpin", "total_spin", "SpinRate"),
                        carry_distance=get_val("CarryDistance", "carry_distance"),
                        total_distance=get_val("TotalDistance", "total_distance"),
                        side_spin=get_val("SideSpin", "side_spin"),
                        back_spin=get_val("BackSpin", "back_spin"),
                        launch_direction=get_val("LaunchDirection", "launch_direction"),
                        apex_height=get_val("ApexHeight", "apex_height"),
                        descent_angle=get_val("DescentAngle", "descent_angle"),
                        smash_factor=get_val("SmashFactor", "smash_factor"),
                        dynamic_loft=get_val("DynamicLoft", "dynamic_loft"),
                        attack_angle=get_val("AttackAngle", "attack_angle"),
                        club_path=get_val("ClubPath", "club_path"),
                        face_angle=get_val("FaceAngle", "face_angle"),
                        dtl_video_path=dtl_video_path,
                        face_video_path=face_video_path,
                        putting_video_path=putting_video_path,
                        raw_json=raw_json_str,
                    )
                    session.add(shot)
                    session.flush()
                    shot_id = shot.id
                logger.info("Shot logged for session %s (id=%d)", self._active_session_id, shot_id)
                return shot_id
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("Database write failed (attempt %d/%d), retrying: %s", attempt + 1, max_retries, e)
                    import time
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error("Failed to log shot after %d attempts: %s", max_retries, e, exc_info=True)
                    raise

    def active_session_id(self) -> Optional[int]:
        return self._active_session_id

    def update_session(self, session_id: int, name: Optional[str] = None, notes: Optional[str] = None, club: Optional[str] = None, session_type: Optional[str] = None, tags: Optional[list[str]] = None, is_favorite: Optional[bool] = None, custom_fields: Optional[str] = None) -> bool:
        """Update session fields."""
        try:
            with Session(self.engine) as session, session.begin():
                record = session.get(SessionModel, session_id)
                if not record:
                    return False
                
                if name is not None:
                    record.name = name
                if notes is not None:
                    record.notes = notes
                if club is not None:
                    record.club = club
                if session_type is not None:
                    record.session_type = session_type
                if tags is not None:
                    record.tags = json.dumps(tags)
                if is_favorite is not None:
                    record.is_favorite = is_favorite
                if custom_fields is not None:
                    record.custom_fields = custom_fields
            
            logger.debug("Updated session %d", session_id)
            return True
        except Exception as e:
            logger.error("Error updating session: %s", e, exc_info=True)
            return False

    def update_shot(self, shot_id: int, tags: Optional[list[str]] = None, is_favorite: Optional[bool] = None, notes: Optional[str] = None, custom_fields: Optional[str] = None) -> bool:
        """Update shot fields."""
        try:
            with Session(self.engine) as session, session.begin():
                shot = session.get(ShotModel, shot_id)
                if not shot:
                    return False
                
                if tags is not None:
                    shot.tags = json.dumps(tags)
                if is_favorite is not None:
                    shot.is_favorite = is_favorite
                if notes is not None:
                    shot.notes = notes
                if custom_fields is not None:
                    shot.custom_fields = custom_fields
            
            logger.debug("Updated shot %d", shot_id)
            return True
        except Exception as e:
            logger.error("Error updating shot: %s", e, exc_info=True)
            return False

    def delete_session(self, session_id: int) -> bool:
        """Delete session, all its shots, and associated video files."""
        try:
            video_files_to_delete = []
            
            with Session(self.engine) as session:
                record = session.get(SessionModel, session_id)
                if not record:
                    return False
                
                # Get all shots for this session to collect video paths
                shots = session.query(ShotModel).filter(ShotModel.session_id == session_id).all()
                
                # Collect video file paths and their thumbnails
                for shot in shots:
                    if shot.dtl_video_path:
                        video_path = Path(shot.dtl_video_path)
                        if video_path.exists():
                            video_files_to_delete.append(video_path)
                            # Also delete thumbnail if it exists
                            thumbnail_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
                            if thumbnail_path.exists():
                                video_files_to_delete.append(thumbnail_path)
                    if shot.face_video_path:
                        video_path = Path(shot.face_video_path)
                        if video_path.exists():
                            video_files_to_delete.append(video_path)
                            # Also delete thumbnail if it exists
                            thumbnail_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
                            if thumbnail_path.exists():
                                video_files_to_delete.append(thumbnail_path)
                    if shot.putting_video_path:
                        video_path = Path(shot.putting_video_path)
                        if video_path.exists():
                            video_files_to_delete.append(video_path)
                            # Also delete thumbnail if it exists
                            thumbnail_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
                            if thumbnail_path.exists():
                                video_files_to_delete.append(thumbnail_path)
                
                # Delete shots and session
                session.query(ShotModel).filter(ShotModel.session_id == session_id).delete()
                session.delete(record)
                session.commit()
            
            # Delete video files and thumbnails after database transaction
            deleted_files = 0
            for file_path in video_files_to_delete:
                try:
                    file_path.unlink()
                    deleted_files += 1
                    logger.debug("Deleted file: %s", file_path)
                except Exception as e:
                    logger.warning("Failed to delete file %s: %s", file_path, e)
            
            logger.info("Deleted session %d (removed %d files including videos and thumbnails)", session_id, deleted_files)
            return True
        except Exception as e:
            logger.error("Error deleting session: %s", e, exc_info=True)
            return False

    def get_all_sessions(self) -> list[SessionModel]:
        """Get all sessions ordered by start time."""
        with Session(self.engine) as session:
            return list(session.query(SessionModel).order_by(SessionModel.started_at.desc()).all())

    def get_session_shots(self, session_id: int) -> list[ShotModel]:
        """Get all shots for a session."""
        with Session(self.engine) as session:
            return list(session.query(ShotModel).filter(ShotModel.session_id == session_id).order_by(ShotModel.recorded_at).all())
