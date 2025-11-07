"""
Swing Flaw Detector
Identifies biomechanical issues in golf swings and provides coaching recommendations
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FlawDetector:
    """
    Analyzes swing metrics to identify flaws and provide recommendations.
    Compares user metrics against ideal ranges and professional benchmarks.
    """
    
    def __init__(self):
        # Define ideal ranges for each metric
        # Format: (min_ideal, max_ideal)
        self.ideal_ranges = {
            'hip_rotation': (35, 50),           # degrees
            'shoulder_rotation': (80, 110),     # degrees
            'x_factor': (35, 55),               # degrees (shoulder-hip separation)
            'spine_angle': (25, 40),            # degrees forward tilt
            'spine_angle_change': (-5, 5),      # degrees (maintain angle)
            'weight_transfer': (0.05, 0.15),    # normalized units
            'tempo_ratio': (2.5, 3.5),          # backswing:downswing ratio
            'backswing_time': (0.7, 1.1),       # seconds
            'downswing_time': (0.2, 0.35),      # seconds
            'club_speed': (85, 125)             # mph (very wide range)
        }
        
        logger.info("FlawDetector initialized")
    
    async def detect_flaws(self, user_metrics: Dict, 
                          pro_reference: Optional[Dict] = None) -> Dict:
        """
        Analyze swing metrics and detect flaws.
        
        Args:
            user_metrics: User's swing metrics
            pro_reference: Optional matched pro's metrics for comparison
            
        Returns:
            Dictionary containing flaws, score, and recommendations
        """
        logger.info("Analyzing swing for flaws...")
        
        flaws = []
        
        # Check each metric against ideal ranges
        for metric, (min_val, max_val) in self.ideal_ranges.items():
            if metric not in user_metrics:
                continue
            
            user_val = user_metrics[metric]
            
            # Check if outside ideal range
            if user_val < min_val:
                severity = self._calculate_severity(user_val, min_val, 'low')
                flaw = {
                    'metric': metric,
                    'metric_display': metric.replace('_', ' ').title(),
                    'value': round(user_val, 2),
                    'ideal_min': min_val,
                    'ideal_max': max_val,
                    'issue': 'too_low',
                    'severity_level': severity['level'],
                    'severity_score': severity['score'],
                    'recommendation': self._get_recommendation(metric, 'too_low')
                }
                flaws.append(flaw)
                
            elif user_val > max_val:
                severity = self._calculate_severity(user_val, max_val, 'high')
                flaw = {
                    'metric': metric,
                    'metric_display': metric.replace('_', ' ').title(),
                    'value': round(user_val, 2),
                    'ideal_min': min_val,
                    'ideal_max': max_val,
                    'issue': 'too_high',
                    'severity_level': severity['level'],
                    'severity_score': severity['score'],
                    'recommendation': self._get_recommendation(metric, 'too_high')
                }
                flaws.append(flaw)
        
        # Sort by severity
        flaws.sort(key=lambda x: x['severity_score'], reverse=True)
        
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
            diff_pct = (threshold - value) / threshold
        else:
            diff_pct = (value - threshold) / threshold
        
        if diff_pct >= 0.50:
            level = 'major'
        elif diff_pct >= 0.30:
            level = 'moderate'
        else:
            level = 'minor'
        
        return {'level': level, 'score': min(diff_pct, 1.0)}
    
    def _get_recommendation(self, metric: str, issue: str) -> str:
        """Get coaching recommendation for a flaw"""
        recommendations = {
            ('hip_rotation', 'too_low'): 
                "Increase hip turn in backswing. Focus on rotating around your spine.",
            ('shoulder_rotation', 'too_low'):
                "Turn shoulders more fully. Try to get your back facing the target.",
            ('x_factor', 'too_low'):
                "Create more separation between shoulders and hips. Resist with lower body.",
            ('weight_transfer', 'too_low'):
                "Shift weight more to front foot through impact.",
            ('tempo_ratio', 'too_low'):
                "Slow down your backswing. Try 3:1 tempo.",
        }
        return recommendations.get((metric, issue), "Work with a coach on this aspect.")
    
    def _calculate_overall_score(self, flaws: List[Dict]) -> float:
        """Calculate swing score (0-100)"""
        score = 100.0
        for flaw in flaws:
            if flaw['severity_level'] == 'major':
                score -= 15
            elif flaw['severity_level'] == 'moderate':
                score -= 10
            else:
                score -= 5
        return max(0, round(score, 1))


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        detector = FlawDetector()
        test_metrics = {
            'hip_rotation': 28,
            'shoulder_rotation': 75,
            'x_factor': 47,
            'weight_transfer': 0.04,
            'tempo_ratio': 2.2
        }
        result = await detector.detect_flaws(test_metrics)
        print(f"\nScore: {result['overall_score']}/100")
        print(f"Flaws found: {result['flaw_count']}")
        for flaw in result['flaws'][:3]:
            print(f"\n- {flaw['metric_display']}: {flaw['recommendation']}")
    
    asyncio.run(test())
