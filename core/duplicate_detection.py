"""
Duplicate detection and merge functionality for shots.

This module provides functionality to detect duplicate shots based on:
- Time proximity (shots within 5 seconds)
- Metric similarity (club speed, ball speed, launch angle, etc.)
- Session context (same session more likely to have duplicates)

Duplicate detection uses a similarity scoring algorithm that considers
multiple factors. Shots with similarity scores above a threshold are
flagged as potential duplicates.

The merge functionality combines data from two shots, preferring one
over the other or merging values intelligently.

Usage:
    from core.duplicate_detection import find_duplicates, merge_shots
    
    # Find duplicates in a list of shots
    duplicates = find_duplicates(shots, similarity_threshold=0.8)
    for match in duplicates:
        print(f"Shots {match.shot1_id} and {match.shot2_id} are duplicates")
    
    # Merge two shots
    merged = merge_shots(shot1, shot2, prefer="first")
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class DuplicateMatch:
    """
    Represents a potential duplicate match between two shots.
    
    Attributes:
        shot1_id: ID of first shot
        shot2_id: ID of second shot
        similarity_score: Similarity score (0.0 to 1.0)
        reason: Human-readable reason for the match
    """
    
    def __init__(self, shot1_id: int, shot2_id: int, similarity_score: float, reason: str):
        self.shot1_id = shot1_id
        self.shot2_id = shot2_id
        self.similarity_score = similarity_score
        self.reason = reason
    
    def __repr__(self) -> str:
        return f"DuplicateMatch(shot1={self.shot1_id}, shot2={self.shot2_id}, score={self.similarity_score:.2f}, reason={self.reason})"


def calculate_similarity(shot1: dict, shot2: dict) -> tuple[float, str]:
    """
    Calculate similarity score between two shots (0.0 to 1.0).
    
    Args:
        shot1: First shot dictionary
        shot2: Second shot dictionary
    
    Returns:
        Tuple of (similarity_score, reason)
    """
    score = 0.0
    reasons = []
    
    # Time-based similarity (shots within 5 seconds are likely duplicates)
    time1 = shot1.get("recorded_at")
    time2 = shot2.get("recorded_at")
    
    if time1 and time2:
        if isinstance(time1, str):
            try:
                time1 = datetime.fromisoformat(time1.replace("Z", "+00:00"))
            except:
                time1 = None
        if isinstance(time2, str):
            try:
                time2 = datetime.fromisoformat(time2.replace("Z", "+00:00"))
            except:
                time2 = None
        
        if time1 and time2:
            time_diff = abs((time1 - time2).total_seconds())
            if time_diff < 5:
                time_score = max(0, 1.0 - (time_diff / 5.0))
                score += time_score * 0.4  # 40% weight for time
                reasons.append(f"Time difference: {time_diff:.1f}s")
    
    # Metric-based similarity
    metric_keys = [
        "club_speed", "ball_speed", "launch_angle", "spin_rate",
        "carry_distance", "total_distance", "smash_factor"
    ]
    
    metric_matches = 0
    metric_total = 0
    
    for key in metric_keys:
        val1 = shot1.get(key) or shot1.get(key.replace("_", "").title())
        val2 = shot2.get(key) or shot2.get(key.replace("_", "").title())
        
        if val1 is not None and val2 is not None:
            try:
                val1_float = float(val1)
                val2_float = float(val2)
                
                # Calculate relative difference
                if val1_float != 0:
                    diff = abs(val1_float - val2_float) / abs(val1_float)
                    if diff < 0.05:  # Within 5%
                        metric_matches += 1
                    metric_total += 1
            except (ValueError, TypeError):
                pass
    
    if metric_total > 0:
        metric_score = metric_matches / metric_total
        score += metric_score * 0.5  # 50% weight for metrics
        reasons.append(f"Metric match: {metric_matches}/{metric_total}")
    
    # Session-based similarity (same session increases likelihood)
    session1 = shot1.get("session_id")
    session2 = shot2.get("session_id")
    
    if session1 and session2 and session1 == session2:
        score += 0.1  # 10% bonus for same session
        reasons.append("Same session")
    
    # Normalize score to 0-1 range
    score = min(1.0, score)
    
    reason = "; ".join(reasons) if reasons else "No matching criteria"
    
    return (score, reason)


def find_duplicates(
    shots: list[dict],
    similarity_threshold: float = 0.8,
    max_time_diff_seconds: int = 10
) -> list[DuplicateMatch]:
    """
    Find potential duplicate shots.
    
    Args:
        shots: List of shot dictionaries (each should have an 'id' field)
        similarity_threshold: Minimum similarity score to consider duplicates (0.0-1.0)
        max_time_diff_seconds: Maximum time difference in seconds to consider
    
    Returns:
        List of DuplicateMatch objects
    """
    duplicates = []
    checked_pairs = set()
    
    for i, shot1 in enumerate(shots):
        shot1_id = shot1.get("id", i)
        
        for j, shot2 in enumerate(shots[i+1:], start=i+1):
            shot2_id = shot2.get("id", j)
            
            # Skip if already checked (bidirectional)
            pair_key = tuple(sorted([shot1_id, shot2_id]))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            
            # Check time difference first (quick filter)
            time1 = shot1.get("recorded_at")
            time2 = shot2.get("recorded_at")
            
            if time1 and time2:
                if isinstance(time1, str):
                    try:
                        time1 = datetime.fromisoformat(time1.replace("Z", "+00:00"))
                    except:
                        time1 = None
                if isinstance(time2, str):
                    try:
                        time2 = datetime.fromisoformat(time2.replace("Z", "+00:00"))
                    except:
                        time2 = None
                
                if time1 and time2:
                    time_diff = abs((time1 - time2).total_seconds())
                    if time_diff > max_time_diff_seconds:
                        continue  # Too far apart in time
            
            # Calculate similarity
            similarity, reason = calculate_similarity(shot1, shot2)
            
            if similarity >= similarity_threshold:
                duplicates.append(
                    DuplicateMatch(shot1_id, shot2_id, similarity, reason)
                )
    
    # Sort by similarity score (highest first)
    duplicates.sort(key=lambda x: x.similarity_score, reverse=True)
    
    return duplicates


def merge_shots(shot1: dict, shot2: dict, prefer: str = "first") -> dict:
    """
    Merge two shot dictionaries, preferring non-None values.
    
    Args:
        shot1: First shot dictionary
        shot2: Second shot dictionary
        prefer: "first" or "second" to prefer values when both exist
    
    Returns:
        Merged shot dictionary
    """
    merged = {}
    
    # Start with preferred shot
    base_shot = shot1 if prefer == "first" else shot2
    other_shot = shot2 if prefer == "first" else shot1
    
    # Copy all keys from base shot
    for key, value in base_shot.items():
        merged[key] = value
    
    # Fill in missing values from other shot
    for key, value in other_shot.items():
        if key not in merged or merged[key] is None:
            merged[key] = value
        elif prefer == "first" and value is not None:
            # Prefer non-None values
            merged[key] = value
    
    # Merge lists (tags, etc.)
    if "tags" in shot1 or "tags" in shot2:
        tags1 = shot1.get("tags", [])
        tags2 = shot2.get("tags", [])
        if isinstance(tags1, str):
            import json
            try:
                tags1 = json.loads(tags1)
            except:
                tags1 = []
        if isinstance(tags2, str):
            import json
            try:
                tags2 = json.loads(tags2)
            except:
                tags2 = []
        merged["tags"] = list(set(tags1 + tags2))
    
    # Merge notes
    notes1 = shot1.get("notes", "")
    notes2 = shot2.get("notes", "")
    if notes1 and notes2 and notes1 != notes2:
        merged["notes"] = f"{notes1}\n--- Merged from duplicate ---\n{notes2}"
    elif notes2 and not notes1:
        merged["notes"] = notes2
    
    # Prefer favorite if either is favorite
    merged["is_favorite"] = shot1.get("is_favorite", False) or shot2.get("is_favorite", False)
    
    # Use earlier recorded_at time
    time1 = shot1.get("recorded_at")
    time2 = shot2.get("recorded_at")
    if time1 and time2:
        if isinstance(time1, str):
            try:
                time1 = datetime.fromisoformat(time1.replace("Z", "+00:00"))
            except:
                time1 = None
        if isinstance(time2, str):
            try:
                time2 = datetime.fromisoformat(time2.replace("Z", "+00:00"))
            except:
                time2 = None
        
        if time1 and time2:
            merged["recorded_at"] = min(time1, time2)
    
    return merged


def detect_and_merge_duplicates(
    session_manager,
    similarity_threshold: float = 0.85,
    dry_run: bool = True
) -> dict:
    """
    Detect and optionally merge duplicate shots in the database.
    
    Args:
        session_manager: SessionManager instance
        similarity_threshold: Minimum similarity to consider duplicates
        dry_run: If True, only detect duplicates without merging
    
    Returns:
        Dictionary with detection results
    """
    from sqlalchemy.orm import Session
    from core.session_manager import ShotModel
    
    results = {
        "duplicates_found": 0,
        "duplicates_merged": 0,
        "shots_removed": 0,
        "matches": [],
    }
    
    try:
        with Session(session_manager.engine) as db_session:
            # Get all shots
            all_shots = db_session.query(ShotModel).order_by(ShotModel.recorded_at).all()
            
            if len(all_shots) < 2:
                logger.info("Not enough shots to check for duplicates")
                return results
            
            # Convert to dictionaries for comparison
            shots_dict = []
            for shot in all_shots:
                shot_dict = {
                    "id": shot.id,
                    "session_id": shot.session_id,
                    "recorded_at": shot.recorded_at.isoformat() if shot.recorded_at else None,
                    "club_speed": shot.club_speed,
                    "ball_speed": shot.ball_speed,
                    "launch_angle": shot.launch_angle,
                    "spin_rate": shot.spin_rate,
                    "carry_distance": shot.carry_distance,
                    "total_distance": shot.total_distance,
                    "smash_factor": shot.smash_factor,
                    "tags": shot.tags,
                    "notes": shot.notes,
                    "is_favorite": shot.is_favorite,
                }
                shots_dict.append(shot_dict)
            
            # Find duplicates
            duplicates = find_duplicates(shots_dict, similarity_threshold)
            results["duplicates_found"] = len(duplicates)
            results["matches"] = [
                {
                    "shot1_id": match.shot1_id,
                    "shot2_id": match.shot2_id,
                    "similarity": match.similarity_score,
                    "reason": match.reason,
                }
                for match in duplicates
            ]
            
            if dry_run:
                logger.info("Dry run: Found %d potential duplicate pairs", len(duplicates))
                return results
            
            # Merge duplicates (keep first, remove second)
            merged_shots = set()
            removed_shots = []
            
            for match in duplicates:
                if match.shot1_id in merged_shots or match.shot2_id in merged_shots:
                    continue  # Already processed
                
                shot1 = db_session.get(ShotModel, match.shot1_id)
                shot2 = db_session.get(ShotModel, match.shot2_id)
                
                if not shot1 or not shot2:
                    continue
                
                # Convert to dicts for merging
                shot1_dict = {
                    "id": shot1.id,
                    "session_id": shot1.session_id,
                    "recorded_at": shot1.recorded_at.isoformat() if shot1.recorded_at else None,
                    "club_speed": shot1.club_speed,
                    "ball_speed": shot1.ball_speed,
                    "launch_angle": shot1.launch_angle,
                    "spin_rate": shot1.spin_rate,
                    "carry_distance": shot1.carry_distance,
                    "total_distance": shot1.total_distance,
                    "smash_factor": shot1.smash_factor,
                    "tags": shot1.tags,
                    "notes": shot1.notes,
                    "is_favorite": shot1.is_favorite,
                }
                
                shot2_dict = {
                    "id": shot2.id,
                    "session_id": shot2.session_id,
                    "recorded_at": shot2.recorded_at.isoformat() if shot2.recorded_at else None,
                    "club_speed": shot2.club_speed,
                    "ball_speed": shot2.ball_speed,
                    "launch_angle": shot2.launch_angle,
                    "spin_rate": shot2.spin_rate,
                    "carry_distance": shot2.carry_distance,
                    "total_distance": shot2.total_distance,
                    "smash_factor": shot2.smash_factor,
                    "tags": shot2.tags,
                    "notes": shot2.notes,
                    "is_favorite": shot2.is_favorite,
                }
                
                # Merge (prefer shot1)
                merged = merge_shots(shot1_dict, shot2_dict, prefer="first")
                
                # Update shot1 with merged data
                if merged.get("tags"):
                    import json
                    shot1.tags = json.dumps(merged["tags"]) if isinstance(merged["tags"], list) else merged["tags"]
                if merged.get("notes"):
                    shot1.notes = merged["notes"]
                if merged.get("is_favorite"):
                    shot1.is_favorite = merged["is_favorite"]
                
                # Remove shot2
                removed_shots.append(shot2.id)
                db_session.delete(shot2)
                
                merged_shots.add(match.shot1_id)
                merged_shots.add(match.shot2_id)
            
            db_session.commit()
            
            results["duplicates_merged"] = len(merged_shots) // 2
            results["shots_removed"] = len(removed_shots)
            
            logger.info(
                "Merged %d duplicate pairs, removed %d shots",
                results["duplicates_merged"],
                results["shots_removed"]
            )
    
    except Exception as e:
        logger.error("Error detecting/merging duplicates: %s", e, exc_info=True)
        results["error"] = str(e)
    
    return results

