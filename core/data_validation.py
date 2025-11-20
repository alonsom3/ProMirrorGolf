"""
Data validation for shot metrics to flag anomalies and impossible values.

This module provides validation functions to check shot data for:
- Out-of-range values (e.g., ball speed > 200 mph)
- Impossible relationships (e.g., ball speed > club speed * 1.5)
- Inconsistent metrics (e.g., total distance < carry distance)
- NaN or infinite values
- Invalid data types

Validation results include warnings (suspicious but possible) and errors
(impossible or invalid). The validation is used during:
- Shot logging (MainWindow.add_shot)
- Data import (CSV/Excel import)
- Manual data entry

Usage:
    from core.data_validation import validate_shot_data_dict
    
    result = validate_shot_data_dict({
        "ClubSpeed": 100.0,
        "BallSpeed": 150.0,
        "CarryDistance": 250.0
    })
    
    if not result.is_valid:
        print("Errors:", result.errors)
    if result.has_issues():
        print("Warnings:", result.warnings)
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Reasonable ranges for golf shot metrics (in appropriate units)
# These ranges are used to flag potentially invalid data
METRIC_RANGES = {
    "club_speed": (0, 150),  # mph
    "ball_speed": (0, 200),  # mph
    "launch_angle": (-20, 45),  # degrees
    "spin_rate": (0, 10000),  # rpm
    "carry_distance": (0, 400),  # yards
    "total_distance": (0, 500),  # yards
    "side_spin": (-5000, 5000),  # rpm
    "back_spin": (0, 10000),  # rpm
    "launch_direction": (-45, 45),  # degrees
    "apex_height": (0, 200),  # yards
    "descent_angle": (0, 90),  # degrees
    "smash_factor": (0, 2.0),  # ratio
    "dynamic_loft": (-20, 60),  # degrees
    "attack_angle": (-20, 20),  # degrees
    "club_path": (-20, 20),  # degrees
    "face_angle": (-30, 30),  # degrees
}


class ValidationResult:
    """Result of data validation."""
    
    def __init__(self, is_valid: bool, warnings: list[str] = None, errors: list[str] = None):
        self.is_valid = is_valid
        self.warnings = warnings or []
        self.errors = errors or []
    
    def has_issues(self) -> bool:
        """Check if there are any warnings or errors."""
        return len(self.warnings) > 0 or len(self.errors) > 0


def validate_shot_data(shot_data: dict) -> ValidationResult:
    """
    Validate shot data for anomalies and impossible values.
    
    Args:
        shot_data: Dictionary containing shot metrics
    
    Returns:
        ValidationResult with validation status and issues
    """
    warnings = []
    errors = []
    
    # Check each metric
    for metric_name, (min_val, max_val) in METRIC_RANGES.items():
        value = shot_data.get(metric_name)
        
        if value is None:
            continue  # Missing values are OK (optional fields)
        
        try:
            value_float = float(value)
            
            # Check if value is outside reasonable range
            if value_float < min_val or value_float > max_val:
                if abs(value_float - min_val) > abs(max_val - min_val) * 0.5:
                    # Very far outside range - error
                    errors.append(
                        f"{metric_name.replace('_', ' ').title()}: {value_float:.2f} "
                        f"is outside reasonable range ({min_val} - {max_val})"
                    )
                else:
                    # Slightly outside range - warning
                    warnings.append(
                        f"{metric_name.replace('_', ' ').title()}: {value_float:.2f} "
                        f"is outside typical range ({min_val} - {max_val})"
                    )
            
            # Check for NaN or infinite values
            if not (-1e10 < value_float < 1e10):
                errors.append(
                    f"{metric_name.replace('_', ' ').title()}: Invalid value (NaN or infinite)"
                )
        
        except (ValueError, TypeError):
            errors.append(
                f"{metric_name.replace('_', ' ').title()}: Invalid value type"
            )
    
    # Cross-metric validation
    club_speed = shot_data.get("club_speed")
    ball_speed = shot_data.get("ball_speed")
    
    if club_speed is not None and ball_speed is not None:
        try:
            club_speed_float = float(club_speed)
            ball_speed_float = float(ball_speed)
            
            # Ball speed should not exceed club speed by more than 50% (smash factor ~1.5)
            if ball_speed_float > club_speed_float * 1.5:
                errors.append(
                    f"Ball speed ({ball_speed_float:.1f} mph) is unrealistically high "
                    f"compared to club speed ({club_speed_float:.1f} mph)"
                )
            
            # Ball speed should generally be higher than club speed (smash factor > 1.0)
            if ball_speed_float < club_speed_float * 0.8:
                warnings.append(
                    f"Ball speed ({ball_speed_float:.1f} mph) is low compared to "
                    f"club speed ({club_speed_float:.1f} mph) - check for misread"
                )
        
        except (ValueError, TypeError):
            pass
    
    # Check smash factor consistency
    smash_factor = shot_data.get("smash_factor")
    if smash_factor is not None and club_speed is not None and ball_speed is not None:
        try:
            smash_factor_float = float(smash_factor)
            club_speed_float = float(club_speed)
            ball_speed_float = float(ball_speed)
            
            if club_speed_float > 0:
                calculated_smash = ball_speed_float / club_speed_float
                if abs(smash_factor_float - calculated_smash) > 0.1:
                    warnings.append(
                        f"Smash factor ({smash_factor_float:.2f}) doesn't match "
                        f"calculated value ({calculated_smash:.2f})"
                    )
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    
    # Check distance consistency
    carry_distance = shot_data.get("carry_distance")
    total_distance = shot_data.get("total_distance")
    
    if carry_distance is not None and total_distance is not None:
        try:
            carry_float = float(carry_distance)
            total_float = float(total_distance)
            
            # Total distance should be >= carry distance
            if total_float < carry_float:
                errors.append(
                    f"Total distance ({total_float:.1f} yds) is less than "
                    f"carry distance ({carry_float:.1f} yds)"
                )
            
            # Total distance shouldn't exceed carry by more than 50 yards typically
            if total_float > carry_float + 50:
                warnings.append(
                    f"Total distance ({total_float:.1f} yds) is much greater than "
                    f"carry distance ({carry_float:.1f} yds) - verify roll distance"
                )
        except (ValueError, TypeError):
            pass
    
    # Check spin consistency
    total_spin = shot_data.get("spin_rate")
    side_spin = shot_data.get("side_spin")
    back_spin = shot_data.get("back_spin")
    
    if total_spin is not None and side_spin is not None and back_spin is not None:
        try:
            total_spin_float = float(total_spin)
            side_spin_float = abs(float(side_spin))
            back_spin_float = float(back_spin)
            
            # Total spin should be approximately sqrt(side_spin^2 + back_spin^2)
            calculated_total = (side_spin_float ** 2 + back_spin_float ** 2) ** 0.5
            
            if abs(total_spin_float - calculated_total) > 500:  # Allow 500 rpm tolerance
                warnings.append(
                    f"Total spin ({total_spin_float:.0f} rpm) doesn't match "
                    f"calculated spin from components ({calculated_total:.0f} rpm)"
                )
        except (ValueError, TypeError):
            pass
    
    is_valid = len(errors) == 0
    
    return ValidationResult(is_valid, warnings, errors)


def validate_shot_data_dict(shot_data: dict) -> ValidationResult:
    """
    Validate shot data dictionary (handles both snake_case and CamelCase keys).
    
    Args:
        shot_data: Dictionary with shot metrics (can use various key formats)
    
    Returns:
        ValidationResult
    """
    # Normalize keys to snake_case
    normalized_data = {}
    
    key_mapping = {
        "ClubSpeed": "club_speed",
        "BallSpeed": "ball_speed",
        "LaunchAngle": "launch_angle",
        "TotalSpin": "spin_rate",
        "SpinRate": "spin_rate",
        "CarryDistance": "carry_distance",
        "TotalDistance": "total_distance",
        "SideSpin": "side_spin",
        "BackSpin": "back_spin",
        "LaunchDirection": "launch_direction",
        "ApexHeight": "apex_height",
        "DescentAngle": "descent_angle",
        "SmashFactor": "smash_factor",
        "DynamicLoft": "dynamic_loft",
        "AttackAngle": "attack_angle",
        "ClubPath": "club_path",
        "FaceAngle": "face_angle",
    }
    
    for key, value in shot_data.items():
        normalized_key = key_mapping.get(key, key.lower().replace(" ", "_"))
        normalized_data[normalized_key] = value
    
    return validate_shot_data(normalized_data)


def flag_anomalies(shots: list[dict]) -> dict[int, ValidationResult]:
    """
    Flag anomalies in a list of shots.
    
    Args:
        shots: List of shot dictionaries (each should have an 'id' field)
    
    Returns:
        Dictionary mapping shot ID to ValidationResult
    """
    results = {}
    
    for idx, shot in enumerate(shots):
        shot_id = shot.get("id", idx)
        result = validate_shot_data_dict(shot)
        results[shot_id] = result
    
    return results

