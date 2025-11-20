"""
Data import functionality for CSV and Excel files.

This module provides functions to import shot data from CSV and Excel files
into the ProMirrorGolf database. It handles:
- CSV file parsing with flexible column mapping
- Excel file parsing (supports .xlsx and .xls formats)
- Automatic data validation using core.data_validation
- Session creation or appending to existing sessions
- Error handling and logging

Usage:
    from core.data_import import import_shots_from_csv, import_shots_from_excel
    
    # Import from CSV
    session_id, count = import_shots_from_csv(
        csv_path=Path("data.csv"),
        session_manager=session_manager,
        create_session=True,
        session_name="Imported Session"
    )
    
    # Import from Excel
    session_id, count = import_shots_from_excel(
        excel_path=Path("data.xlsx"),
        session_manager=session_manager,
        session_id=existing_session_id
    )
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def import_shots_from_csv(
    csv_path: Path,
    session_manager,
    session_id: Optional[int] = None,
    create_session: bool = True,
    session_name: Optional[str] = None,
) -> tuple[int, int]:
    """
    Import shots from a CSV file.
    
    Args:
        csv_path: Path to the CSV file
        session_manager: SessionManager instance
        session_id: Optional existing session ID to add shots to
        create_session: If True and session_id is None, create a new session
        session_name: Name for new session (defaults to filename)
    
    Returns:
        Tuple of (session_id, shots_imported)
    """
    if not csv_path.exists():
        logger.error("CSV file not found: %s", csv_path)
        return (-1, 0)
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        
        if df.empty:
            logger.warning("CSV file is empty: %s", csv_path)
            return (-1, 0)
        
        # Create or use session
        if session_id is None and create_session:
            session_name = session_name or csv_path.stem
            session_id = session_manager.start_session(name=session_name)
            logger.info("Created new session %d for import: %s", session_id, session_name)
        elif session_id is None:
            logger.error("No session ID provided and create_session is False")
            return (-1, 0)
        
        # Map CSV columns to shot fields
        column_mapping = {
            # Core metrics
            "club_speed": ["ClubSpeed", "club_speed", "Club Speed", "club speed"],
            "ball_speed": ["BallSpeed", "ball_speed", "Ball Speed", "ball speed"],
            "launch_angle": ["LaunchAngle", "launch_angle", "Launch Angle", "launch angle"],
            "spin_rate": ["TotalSpin", "total_spin", "SpinRate", "spin_rate", "Spin Rate", "spin rate"],
            
            # Distance metrics
            "carry_distance": ["CarryDistance", "carry_distance", "Carry Distance", "carry distance"],
            "total_distance": ["TotalDistance", "total_distance", "Total Distance", "total distance"],
            
            # Spin breakdown
            "side_spin": ["SideSpin", "side_spin", "Side Spin", "side spin"],
            "back_spin": ["BackSpin", "back_spin", "Back Spin", "back spin"],
            
            # Launch metrics
            "launch_direction": ["LaunchDirection", "launch_direction", "Launch Direction", "launch direction"],
            "apex_height": ["ApexHeight", "apex_height", "Apex Height", "apex height"],
            "descent_angle": ["DescentAngle", "descent_angle", "Descent Angle", "descent angle"],
            
            # Club metrics
            "smash_factor": ["SmashFactor", "smash_factor", "Smash Factor", "smash factor"],
            "dynamic_loft": ["DynamicLoft", "dynamic_loft", "Dynamic Loft", "dynamic loft"],
            "attack_angle": ["AttackAngle", "attack_angle", "Attack Angle", "attack angle"],
            "club_path": ["ClubPath", "club_path", "Club Path", "club path"],
            "face_angle": ["FaceAngle", "face_angle", "Face Angle", "face angle"],
            
            # Metadata
            "tags": ["Tags", "tags", "tag"],
            "notes": ["Notes", "notes", "Note", "note"],
            "is_favorite": ["Favorite", "favorite", "IsFavorite", "is_favorite", "Fav", "fav"],
            "recorded_at": ["Date", "date", "Time", "time", "Timestamp", "timestamp", "RecordedAt", "recorded_at"],
        }
        
        # Find matching columns
        field_to_column = {}
        for field, possible_names in column_mapping.items():
            for col in df.columns:
                if col in possible_names or col.lower() in [n.lower() for n in possible_names]:
                    field_to_column[field] = col
                    break
        
        shots_imported = 0
        
        # Import each row as a shot
        for idx, row in df.iterrows():
            try:
                # Build payload dict
                payload = {}
                for field, col_name in field_to_column.items():
                    if col_name in row and pd.notna(row[col_name]):
                        value = row[col_name]
                        
                        # Type conversion
                        if field == "is_favorite":
                            # Handle boolean/string values
                            if isinstance(value, bool):
                                payload[field] = value
                            elif isinstance(value, str):
                                payload[field] = value.lower() in ["true", "yes", "1", "y"]
                            else:
                                payload[field] = bool(value)
                        elif field == "recorded_at":
                            # Try to parse date
                            try:
                                if isinstance(value, str):
                                    # Try common formats
                                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"]:
                                        try:
                                            payload["recorded_at"] = datetime.strptime(value, fmt)
                                            break
                                        except ValueError:
                                            continue
                                elif isinstance(value, datetime):
                                    payload["recorded_at"] = value
                            except Exception:
                                logger.warning("Could not parse date: %s", value)
                        elif field == "tags":
                            # Handle comma-separated tags
                            if isinstance(value, str):
                                tags = [t.strip() for t in value.split(",") if t.strip()]
                                payload["tags"] = tags
                        else:
                            # Numeric fields
                            try:
                                payload[field] = float(value)
                            except (ValueError, TypeError):
                                logger.warning("Could not convert %s to float: %s", field, value)
                
                # Map payload keys to expected format
                mapped_payload = {}
                key_mapping = {
                    "club_speed": "ClubSpeed",
                    "ball_speed": "BallSpeed",
                    "launch_angle": "LaunchAngle",
                    "spin_rate": "TotalSpin",
                    "carry_distance": "CarryDistance",
                    "total_distance": "TotalDistance",
                    "side_spin": "SideSpin",
                    "back_spin": "BackSpin",
                    "launch_direction": "LaunchDirection",
                    "apex_height": "ApexHeight",
                    "descent_angle": "DescentAngle",
                    "smash_factor": "SmashFactor",
                    "dynamic_loft": "DynamicLoft",
                    "attack_angle": "AttackAngle",
                    "club_path": "ClubPath",
                    "face_angle": "FaceAngle",
                }
                
                for key, value in payload.items():
                    if key in key_mapping:
                        mapped_payload[key_mapping[key]] = value
                    elif key not in ["tags", "notes", "is_favorite", "recorded_at"]:
                        mapped_payload[key] = value
                
                # Get metadata
                tags = payload.get("tags", [])
                notes = payload.get("notes")
                is_favorite = payload.get("is_favorite", False)
                recorded_at = payload.get("recorded_at")
                
                # Temporarily set active session
                old_active = session_manager._active_session_id
                session_manager._active_session_id = session_id
                
                try:
                    # Log shot
                    shot_id = session_manager.log_shot(mapped_payload)
                    
                    if shot_id > 0:
                        # Update metadata
                        if tags:
                            session_manager.update_shot(shot_id, tags=tags)
                        if notes:
                            session_manager.update_shot(shot_id, notes=notes)
                        if is_favorite:
                            session_manager.update_shot(shot_id, is_favorite=True)
                        if recorded_at:
                            # Update recorded_at timestamp
                            from sqlalchemy.orm import Session as DBSession
                            with DBSession(session_manager.engine) as db_session, db_session.begin():
                                from core.session_manager import ShotModel
                                shot = db_session.get(ShotModel, shot_id)
                                if shot:
                                    shot.recorded_at = recorded_at
                        
                        shots_imported += 1
                finally:
                    session_manager._active_session_id = old_active
                    
            except Exception as e:
                logger.error("Error importing row %d: %s", idx, e, exc_info=True)
                continue
        
        logger.info("Imported %d shots from CSV: %s", shots_imported, csv_path)
        return (session_id, shots_imported)
        
    except Exception as e:
        logger.error("Error importing CSV: %s", e, exc_info=True)
        return (-1, 0)


def import_shots_from_excel(
    excel_path: Path,
    session_manager,
    session_id: Optional[int] = None,
    create_session: bool = True,
    session_name: Optional[str] = None,
    sheet_name: Optional[str] = None,
) -> tuple[int, int]:
    """
    Import shots from an Excel file.
    
    Args:
        excel_path: Path to the Excel file
        session_manager: SessionManager instance
        session_id: Optional existing session ID to add shots to
        create_session: If True and session_id is None, create a new session
        session_name: Name for new session (defaults to filename)
        sheet_name: Name of sheet to import (defaults to first sheet)
    
    Returns:
        Tuple of (session_id, shots_imported)
    """
    if not excel_path.exists():
        logger.error("Excel file not found: %s", excel_path)
        return (-1, 0)
    
    try:
        # Read Excel
        if sheet_name:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(excel_path)
        
        if df.empty:
            logger.warning("Excel file is empty: %s", excel_path)
            return (-1, 0)
        
        # Create or use session
        if session_id is None and create_session:
            session_name = session_name or excel_path.stem
            session_id = session_manager.start_session(name=session_name)
            logger.info("Created new session %d for import: %s", session_id, session_name)
        elif session_id is None:
            logger.error("No session ID provided and create_session is False")
            return (-1, 0)
        
        # Use same column mapping as CSV
        column_mapping = {
            "club_speed": ["ClubSpeed", "club_speed", "Club Speed", "club speed"],
            "ball_speed": ["BallSpeed", "ball_speed", "Ball Speed", "ball speed"],
            "launch_angle": ["LaunchAngle", "launch_angle", "Launch Angle", "launch angle"],
            "spin_rate": ["TotalSpin", "total_spin", "SpinRate", "spin_rate", "Spin Rate", "spin rate"],
            "carry_distance": ["CarryDistance", "carry_distance", "Carry Distance", "carry distance"],
            "total_distance": ["TotalDistance", "total_distance", "Total Distance", "total distance"],
            "side_spin": ["SideSpin", "side_spin", "Side Spin", "side spin"],
            "back_spin": ["BackSpin", "back_spin", "Back Spin", "back spin"],
            "launch_direction": ["LaunchDirection", "launch_direction", "Launch Direction", "launch direction"],
            "apex_height": ["ApexHeight", "apex_height", "Apex Height", "apex height"],
            "descent_angle": ["DescentAngle", "descent_angle", "Descent Angle", "descent angle"],
            "smash_factor": ["SmashFactor", "smash_factor", "Smash Factor", "smash factor"],
            "dynamic_loft": ["DynamicLoft", "dynamic_loft", "Dynamic Loft", "dynamic loft"],
            "attack_angle": ["AttackAngle", "attack_angle", "Attack Angle", "attack angle"],
            "club_path": ["ClubPath", "club_path", "Club Path", "club path"],
            "face_angle": ["FaceAngle", "face_angle", "Face Angle", "face angle"],
            "tags": ["Tags", "tags", "tag"],
            "notes": ["Notes", "notes", "Note", "note"],
            "is_favorite": ["Favorite", "favorite", "IsFavorite", "is_favorite", "Fav", "fav"],
            "recorded_at": ["Date", "date", "Time", "time", "Timestamp", "timestamp", "RecordedAt", "recorded_at"],
        }
        
        # Find matching columns
        field_to_column = {}
        for field, possible_names in column_mapping.items():
            for col in df.columns:
                if col in possible_names or col.lower() in [n.lower() for n in possible_names]:
                    field_to_column[field] = col
                    break
        
        shots_imported = 0
        
        # Import each row as a shot
        for idx, row in df.iterrows():
            try:
                # Build payload dict (same logic as CSV)
                payload = {}
                for field, col_name in field_to_column.items():
                    if col_name in row and pd.notna(row[col_name]):
                        value = row[col_name]
                        
                        if field == "is_favorite":
                            if isinstance(value, bool):
                                payload[field] = value
                            elif isinstance(value, str):
                                payload[field] = value.lower() in ["true", "yes", "1", "y"]
                            else:
                                payload[field] = bool(value)
                        elif field == "recorded_at":
                            try:
                                if isinstance(value, str):
                                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"]:
                                        try:
                                            payload["recorded_at"] = datetime.strptime(value, fmt)
                                            break
                                        except ValueError:
                                            continue
                                elif isinstance(value, datetime):
                                    payload["recorded_at"] = value
                            except Exception:
                                logger.warning("Could not parse date: %s", value)
                        elif field == "tags":
                            if isinstance(value, str):
                                tags = [t.strip() for t in value.split(",") if t.strip()]
                                payload["tags"] = tags
                        else:
                            try:
                                payload[field] = float(value)
                            except (ValueError, TypeError):
                                logger.warning("Could not convert %s to float: %s", field, value)
                
                # Map payload keys
                mapped_payload = {}
                key_mapping = {
                    "club_speed": "ClubSpeed",
                    "ball_speed": "BallSpeed",
                    "launch_angle": "LaunchAngle",
                    "spin_rate": "TotalSpin",
                    "carry_distance": "CarryDistance",
                    "total_distance": "TotalDistance",
                    "side_spin": "SideSpin",
                    "back_spin": "BackSpin",
                    "launch_direction": "LaunchDirection",
                    "apex_height": "ApexHeight",
                    "descent_angle": "DescentAngle",
                    "smash_factor": "SmashFactor",
                    "dynamic_loft": "DynamicLoft",
                    "attack_angle": "AttackAngle",
                    "club_path": "ClubPath",
                    "face_angle": "FaceAngle",
                }
                
                for key, value in payload.items():
                    if key in key_mapping:
                        mapped_payload[key_mapping[key]] = value
                    elif key not in ["tags", "notes", "is_favorite", "recorded_at"]:
                        mapped_payload[key] = value
                
                tags = payload.get("tags", [])
                notes = payload.get("notes")
                is_favorite = payload.get("is_favorite", False)
                recorded_at = payload.get("recorded_at")
                
                old_active = session_manager._active_session_id
                session_manager._active_session_id = session_id
                
                try:
                    # Validate shot data before logging
                    from core.data_validation import validate_shot_data_dict
                    validation_result = validate_shot_data_dict(mapped_payload)
                    
                    if validation_result.has_issues():
                        if validation_result.errors:
                            logger.warning("Skipping row %d due to validation errors: %s", idx, validation_result.errors)
                            continue
                        elif validation_result.warnings:
                            logger.info("Row %d has validation warnings: %s", idx, validation_result.warnings)
                    
                    shot_id = session_manager.log_shot(mapped_payload)
                    
                    if shot_id > 0:
                        if tags:
                            session_manager.update_shot(shot_id, tags=tags)
                        if notes:
                            session_manager.update_shot(shot_id, notes=notes)
                        if is_favorite:
                            session_manager.update_shot(shot_id, is_favorite=True)
                        if recorded_at:
                            from sqlalchemy.orm import Session as DBSession
                            with DBSession(session_manager.engine) as db_session, db_session.begin():
                                from core.session_manager import ShotModel
                                shot = db_session.get(ShotModel, shot_id)
                                if shot:
                                    shot.recorded_at = recorded_at
                        
                        shots_imported += 1
                finally:
                    session_manager._active_session_id = old_active
                    
            except Exception as e:
                logger.error("Error importing row %d: %s", idx, e, exc_info=True)
                continue
        
        logger.info("Imported %d shots from Excel: %s", shots_imported, excel_path)
        return (session_id, shots_imported)
        
    except Exception as e:
        logger.error("Error importing Excel: %s", e, exc_info=True)
        return (-1, 0)

