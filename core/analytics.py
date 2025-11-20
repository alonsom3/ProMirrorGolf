"""Advanced analytics functions for golf swing analysis."""

from __future__ import annotations

import logging
import math
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def calculate_consistency_metrics(values: list[float]) -> dict:
    """Calculate consistency metrics (mean, std dev, variance, range).
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with metrics
    """
    if not values:
        return {
            "mean": None,
            "std_dev": None,
            "variance": None,
            "min": None,
            "max": None,
            "range": None,
            "coefficient_of_variation": None,
        }
    
    values_array = np.array(values)
    
    mean = float(np.mean(values_array))
    std_dev = float(np.std(values_array, ddof=1))  # Sample standard deviation
    variance = float(np.var(values_array, ddof=1))
    min_val = float(np.min(values_array))
    max_val = float(np.max(values_array))
    range_val = max_val - min_val
    coefficient_of_variation = (std_dev / mean * 100) if mean != 0 else None
    
    return {
        "mean": mean,
        "std_dev": std_dev,
        "variance": variance,
        "min": min_val,
        "max": max_val,
        "range": range_val,
        "coefficient_of_variation": coefficient_of_variation,
    }


def calculate_tempo_ratio(
    backswing_time: Optional[float],
    downswing_time: Optional[float],
) -> Optional[float]:
    """Calculate tempo ratio (backswing/downswing).
    
    Args:
        backswing_time: Time for backswing in seconds
        downswing_time: Time for downswing in seconds
        
    Returns:
        Tempo ratio or None if data insufficient
    """
    if backswing_time is None or downswing_time is None:
        return None
    
    if downswing_time == 0:
        return None
    
    return backswing_time / downswing_time


def estimate_swing_plane_angle(
    club_path: Optional[float],
    attack_angle: Optional[float],
) -> Optional[float]:
    """Estimate swing plane angle from club path and attack angle.
    
    Args:
        club_path: Club path angle in degrees
        attack_angle: Attack angle in degrees
        
    Returns:
        Estimated swing plane angle in degrees
    """
    if club_path is None or attack_angle is None:
        return None
    
    # Simplified swing plane calculation
    # Swing plane ≈ arctan(attack_angle / club_path)
    # This is a simplified model
    if club_path == 0:
        return None
    
    swing_plane = math.degrees(math.atan(attack_angle / abs(club_path)))
    return swing_plane


def generate_dispersion_heatmap(
    launch_directions: list[float],
    carry_distances: list[float],
    grid_size: int = 20,
) -> dict:
    """Generate heat map data for shot dispersion.
    
    Args:
        launch_directions: List of launch direction values (degrees)
        carry_distances: List of carry distance values (yards)
        grid_size: Number of grid cells (default: 20x20)
        
    Returns:
        Dictionary with heat map data including grid, counts, and bounds
    """
    if not launch_directions or not carry_distances or len(launch_directions) != len(carry_distances):
        return {
            "grid": None,
            "x_bounds": (0, 0),
            "y_bounds": (0, 0),
            "counts": None,
        }
    
    # Filter out None values
    valid_pairs = [(d, c) for d, c in zip(launch_directions, carry_distances) 
                   if d is not None and c is not None]
    
    if not valid_pairs:
        return {
            "grid": None,
            "x_bounds": (0, 0),
            "y_bounds": (0, 0),
            "counts": None,
        }
    
    directions, distances = zip(*valid_pairs)
    
    # Calculate bounds
    min_dir = min(directions)
    max_dir = max(directions)
    min_dist = min(distances)
    max_dist = max(distances)
    
    # Add padding
    dir_range = max_dir - min_dir
    dist_range = max_dist - min_dist
    padding_dir = dir_range * 0.1 if dir_range > 0 else 1.0
    padding_dist = dist_range * 0.1 if dist_range > 0 else 1.0
    
    x_bounds = (min_dir - padding_dir, max_dir + padding_dir)
    y_bounds = (min_dist - padding_dist, max_dist + padding_dist)
    
    # Create grid
    grid = np.zeros((grid_size, grid_size))
    
    # Bin data into grid
    for direction, distance in valid_pairs:
        # Normalize to grid coordinates
        x_norm = (direction - x_bounds[0]) / (x_bounds[1] - x_bounds[0])
        y_norm = (distance - y_bounds[0]) / (y_bounds[1] - y_bounds[0])
        
        # Clamp to valid range
        x_norm = max(0, min(1, x_norm))
        y_norm = max(0, min(1, y_norm))
        
        # Convert to grid indices
        x_idx = int(x_norm * grid_size)
        y_idx = int(y_norm * grid_size)
        
        # Clamp indices
        x_idx = max(0, min(grid_size - 1, x_idx))
        y_idx = max(0, min(grid_size - 1, y_idx))
        
        grid[y_idx, x_idx] += 1
    
    return {
        "grid": grid.tolist(),
        "x_bounds": x_bounds,
        "y_bounds": y_bounds,
        "counts": grid.tolist(),
        "max_count": float(np.max(grid)),
        "total_shots": len(valid_pairs),
    }


def predict_ball_flight(
    ball_speed: float,
    launch_angle: float,
    spin_rate: float,
    launch_direction: Optional[float] = None,
    altitude: float = 0.0,
    temperature: float = 20.0,
) -> dict:
    """Predict ball flight trajectory using physics.
    
    Args:
        ball_speed: Ball speed in mph
        launch_angle: Launch angle in degrees
        spin_rate: Spin rate in rpm
        launch_direction: Launch direction in degrees (left/right)
        altitude: Altitude in feet
        temperature: Temperature in Celsius
        
    Returns:
        Dictionary with predicted flight data
    """
    # Convert units
    speed_ms = ball_speed * 0.44704  # mph to m/s
    angle_rad = math.radians(launch_angle)
    
    # Air density (simplified)
    rho = 1.225 * (1 - 0.0065 * altitude / 288.15) ** 5.256
    
    # Drag coefficient (simplified model)
    cd = 0.3 + (spin_rate / 10000) * 0.1
    
    # Initial velocity components
    vx0 = speed_ms * math.cos(angle_rad)
    vz0 = speed_ms * math.sin(angle_rad)
    
    # Time step
    dt = 0.01
    t = 0
    x = 0
    z = 0
    vx = vx0
    vz = vz0
    
    max_height = 0
    apex_time = 0
    
    # Simulate flight
    while z >= 0:
        # Air resistance
        v = math.sqrt(vx**2 + vz**2)
        drag = 0.5 * rho * cd * v**2
        
        # Gravity
        g = 9.81
        
        # Update velocity
        vx -= (drag * vx / v) * dt if v > 0 else 0
        vz -= (g + (drag * vz / v)) * dt if v > 0 else g * dt
        
        # Update position
        x += vx * dt
        z += vz * dt
        
        # Track max height
        if z > max_height:
            max_height = z
            apex_time = t
        
        t += dt
        
        # Safety limit
        if t > 30:
            break
    
    # Convert back to yards
    carry_distance = x * 1.09361  # meters to yards
    max_height_yards = max_height * 1.09361
    
    # Estimate total distance (simplified)
    roll_factor = 0.1  # Simplified roll
    total_distance = carry_distance * (1 + roll_factor)
    
    return {
        "carry_distance": carry_distance,
        "total_distance": total_distance,
        "max_height": max_height_yards,
        "apex_time": apex_time,
        "flight_time": t,
        "landing_angle": math.degrees(math.atan(abs(vz / vx))) if vx != 0 else 0,
    }


def calculate_trajectory_points(
    ball_speed: float,
    launch_angle: float,
    spin_rate: float,
    launch_direction: Optional[float] = None,
    side_spin: Optional[float] = None,
    altitude: float = 0.0,
    temperature: float = 20.0,
    dt: float = 0.01,
) -> dict:
    """Calculate full 3D trajectory points for visualization.
    
    Args:
        ball_speed: Ball speed in mph
        launch_angle: Launch angle in degrees
        spin_rate: Spin rate in rpm
        launch_direction: Launch direction in degrees (left/right, negative=left)
        side_spin: Side spin in rpm (negative=left, positive=right)
        altitude: Altitude in feet
        temperature: Temperature in Celsius
        dt: Time step in seconds
        
    Returns:
        Dictionary with trajectory arrays:
        - x: Forward distance (yards)
        - y: Lateral distance (yards, left=negative, right=positive)
        - z: Height (yards)
        - t: Time array (seconds)
        - carry_distance: Total carry distance
        - max_height: Maximum height reached
    """
    # Convert units
    speed_ms = ball_speed * 0.44704  # mph to m/s
    angle_rad = math.radians(launch_angle)
    
    # Air density (simplified)
    rho = 1.225 * (1 - 0.0065 * altitude / 288.15) ** 5.256
    
    # Drag coefficient (simplified model)
    cd = 0.3 + (spin_rate / 10000) * 0.1
    
    # Initial velocity components (forward and vertical)
    vx0 = speed_ms * math.cos(angle_rad)  # Forward
    vz0 = speed_ms * math.sin(angle_rad)  # Vertical
    
    # Lateral velocity from launch direction or side spin
    if launch_direction is not None:
        # Launch direction in degrees (negative=left, positive=right)
        lateral_angle_rad = math.radians(launch_direction)
        vy0 = speed_ms * math.sin(lateral_angle_rad) * math.cos(angle_rad)
    elif side_spin is not None:
        # Estimate lateral velocity from side spin (simplified)
        # Side spin causes lateral movement due to Magnus effect
        spin_factor = side_spin / 10000.0  # Normalize
        vy0 = speed_ms * spin_factor * 0.1  # Simplified lateral velocity
    else:
        vy0 = 0.0
    
    # Initialize arrays
    x_points = []
    y_points = []
    z_points = []
    t_points = []
    
    # Initial conditions
    t = 0
    x = 0  # Forward distance
    y = 0  # Lateral distance
    z = 0  # Height
    vx = vx0
    vy = vy0
    vz = vz0
    
    max_height = 0
    
    # Simulate flight
    while z >= 0:
        # Store current position
        x_points.append(x * 1.09361)  # Convert to yards
        y_points.append(y * 1.09361)  # Convert to yards
        z_points.append(z * 1.09361)  # Convert to yards
        t_points.append(t)
        
        # Air resistance
        v = math.sqrt(vx**2 + vy**2 + vz**2)
        if v > 0:
            drag = 0.5 * rho * cd * v**2
            
            # Drag force components (opposite to velocity)
            drag_x = -(drag * vx / v) if v > 0 else 0
            drag_y = -(drag * vy / v) if v > 0 else 0
            drag_z = -(drag * vz / v) if v > 0 else 0
        else:
            drag_x = drag_y = drag_z = 0
        
        # Gravity
        g = 9.81
        
        # Update velocity
        vx += drag_x * dt
        vy += drag_y * dt
        vz -= (g * dt) + (drag_z * dt)
        
        # Update position
        x += vx * dt
        y += vy * dt
        z += vz * dt
        
        # Track max height
        if z > max_height:
            max_height = z
        
        t += dt
        
        # Safety limit
        if t > 30:
            break
    
    # Convert final values to yards
    carry_distance = x * 1.09361
    max_height_yards = max_height * 1.09361
    
    return {
        "x": np.array(x_points),
        "y": np.array(y_points),
        "z": np.array(z_points),
        "t": np.array(t_points),
        "carry_distance": carry_distance,
        "max_height": max_height_yards,
        "flight_time": t,
    }

