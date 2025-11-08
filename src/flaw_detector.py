"""
Swing Flaw Detector
Identifies biomechanical issues and provides coaching recommendations
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FlawDetector:
    """
    Analyzes swing metrics to identify flaws and provide recommendations
    """
    
    def __init__(self):
        # Define ideal ranges for each metric
        # Format: (min_ideal, max_ideal)
        self.ideal_ranges = {
            'hip_rotation_top': (35, 50),           # degrees
            'shoulder_rotation_top': (80, 110),     # degrees
            'x_factor': (35, 55),                   # degrees
            'spine_angle_address': (25, 40),        # degrees
            'spine_angle_change': (-5, 5),          # degrees (should maintain)
            'weight_transfer': (0.05, 0.15),        # normalized
            'tempo_ratio': (2.5, 3.5),              # backswing:downswing
            'backswing_time': (0.7, 1.1),           # seconds
            'downswing_time': (0.2, 0.35),          # seconds
            'club_speed': (85, 125)                  # mph
        }
        
        logger.info("FlawDetector initialized")
    
    def detect_flaws(self, user_metrics: Dict, 
                     pro_reference: Optional[Dict] = None) -> Dict:
        """
        Analyze swing metrics and detect flaws
        
        Args:
            user_metrics: User's swing metrics dictionary
            pro_reference: Optional matched pro's metrics for comparison
            
        Returns:
            Dictionary with flaws, overall_score, and flaw_count
        """
        logger.info("Analyzing swing for flaws...")
        
        flaws = []
        
        # Check each metric against ideal ranges
        for metric, (min_val, max_val) in self.ideal_ranges.items():
            # Handle different metric name variations
            metric_key = metric
            if metric_key not in user_metrics:
                # Try alternative names
                if metric == 'hip_rotation_top' and 'hip_rotation' in user_metrics:
                    metric_key = 'hip_rotation'
                elif metric == 'shoulder_rotation_top' and 'shoulder_rotation' in user_metrics:
                    metric_key = 'shoulder_rotation'
                elif metric == 'spine_angle_address' and 'spine_angle' in user_metrics:
                    metric_key = 'spine_angle'
            
            if metric_key not in user_metrics:
                continue
            
            user_val = user_metrics[metric_key]
            
            # Skip if value is None or invalid
            if user_val is None:
                continue
            
            # Check if outside ideal range
            if user_val < min_val:
                severity = self._calculate_severity(user_val, min_val, 'low')
                flaw = {
                    'metric': metric,
                    'value': round(float(user_val), 2),
                    'ideal_min': min_val,
                    'ideal_max': max_val,
                    'issue': 'too_low',
                    'severity': severity['score'],
                    'recommendation': self._get_recommendation(metric, 'too_low', user_val, min_val)
                }
                flaws.append(flaw)
                
            elif user_val > max_val:
                severity = self._calculate_severity(user_val, max_val, 'high')
                flaw = {
                    'metric': metric,
                    'value': round(float(user_val), 2),
                    'ideal_min': min_val,
                    'ideal_max': max_val,
                    'issue': 'too_high',
                    'severity': severity['score'],
                    'recommendation': self._get_recommendation(metric, 'too_high', user_val, max_val)
                }
                flaws.append(flaw)
        
        # Sort by severity (highest first)
        flaws.sort(key=lambda x: x['severity'], reverse=True)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(flaws)
        
        result = {
            'flaws': flaws,
            'overall_score': overall_score,
            'flaw_count': len(flaws)
        }
        
        logger.info(f"Analysis complete: {len(flaws)} flaws, score: {overall_score:.1f}/100")
        
        return result
    
    def _calculate_severity(self, value: float, threshold: float, direction: str) -> Dict:
        """Calculate severity based on distance from ideal"""
        if direction == 'low':
            diff = threshold - value
            diff_pct = diff / threshold if threshold != 0 else 0
        else:
            diff = value - threshold
            diff_pct = diff / threshold if threshold != 0 else 0
        
        # Severity score: 0-1, where 1 is most severe
        severity_score = min(diff_pct * 2, 1.0)  # Scale so 50% difference = max severity
        
        return {'score': round(severity_score, 2)}
    
    def _get_recommendation(self, metric: str, issue: str, value: float, threshold: float) -> str:
        """Get coaching recommendation for a flaw"""
        recommendations = {
            ('hip_rotation_top', 'too_low'): 
                f"Your hip rotation is {value:.1f}°, below the ideal range of 35-50°. "
                "Focus on rotating your hips more in the backswing. Try the step drill to improve hip turn.",
            ('hip_rotation_top', 'too_high'):
                f"Your hip rotation is {value:.1f}°, above the ideal range. "
                "You may be over-rotating. Focus on maintaining connection between upper and lower body.",
            ('shoulder_rotation_top', 'too_low'):
                f"Your shoulder turn is {value:.1f}°, below the ideal range of 80-110°. "
                "Turn your shoulders more fully. Try to get your back facing the target at the top.",
            ('shoulder_rotation_top', 'too_high'):
                f"Your shoulder turn is {value:.1f}°, above the ideal range. "
                "You may be over-rotating. Focus on maintaining spine angle and connection.",
            ('x_factor', 'too_low'):
                f"Your X-Factor (shoulder-hip separation) is {value:.1f}°, below the ideal range of 35-55°. "
                "Create more separation between shoulders and hips. Resist with your lower body in the backswing.",
            ('x_factor', 'too_high'):
                f"Your X-Factor is {value:.1f}°, above the ideal range. "
                "You may have too much separation. Focus on maintaining connection and sequencing.",
            ('spine_angle_address', 'too_low'):
                f"Your spine angle is {value:.1f}°, below the ideal range of 25-40°. "
                "Stand more upright at address. Check your posture and setup.",
            ('spine_angle_address', 'too_high'):
                f"Your spine angle is {value:.1f}°, above the ideal range. "
                "You may be bending over too much. Check your setup posture.",
            ('spine_angle_change', 'too_low'):
                f"Your spine angle changed by {value:.1f}° (ideal: maintain within -5 to 5°). "
                "You're losing spine angle. Focus on maintaining your posture through impact.",
            ('spine_angle_change', 'too_high'):
                f"Your spine angle changed by {value:.1f}° (ideal: maintain within -5 to 5°). "
                "You're changing spine angle too much. Focus on maintaining posture.",
            ('weight_transfer', 'too_low'):
                f"Your weight transfer is {value:.2f}, below the ideal range of 0.05-0.15. "
                "Shift more weight to your front foot through impact. Practice weight shift drills.",
            ('weight_transfer', 'too_high'):
                f"Your weight transfer is {value:.2f}, above the ideal range. "
                "You may be shifting too aggressively. Focus on controlled weight transfer.",
            ('tempo_ratio', 'too_low'):
                f"Your tempo ratio is {value:.1f}:1, below the ideal range of 2.5-3.5:1. "
                "Slow down your backswing. Aim for a 3:1 tempo ratio (backswing:downswing).",
            ('tempo_ratio', 'too_high'):
                f"Your tempo ratio is {value:.1f}:1, above the ideal range. "
                "Your backswing may be too slow. Find a balanced tempo that feels natural.",
        }
        
        return recommendations.get((metric, issue), 
            f"Work with a coach to improve your {metric.replace('_', ' ')}. "
            f"Your value is {value:.2f}, ideal range is {threshold:.1f}.")
    
    def _calculate_overall_score(self, flaws: List[Dict]) -> float:
        """Calculate overall swing score (0-100)"""
        score = 100.0
        
        for flaw in flaws:
            severity = flaw.get('severity', 0)
            # Deduct points based on severity
            if severity >= 0.7:
                score -= 15  # Major flaw
            elif severity >= 0.4:
                score -= 10  # Moderate flaw
            else:
                score -= 5   # Minor flaw
        
        return max(0, round(score, 1))

