"""
AI Coach Module - Provides personalized coaching recommendations
with historical tracking and improvement analysis
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class AICoach:
    """
    AI-powered coaching assistant that provides personalized recommendations
    based on historical swing data and improvement trends
    """
    
    def __init__(self, swing_db):
        """
        Initialize AI Coach
        
        Args:
            swing_db: SwingDatabase instance for accessing historical data
        """
        self.swing_db = swing_db
        self.recommendation_history = []  # Track recommendations given
        logger.info("AI Coach initialized")
    
    def get_coaching_recommendations(self, user_id: str, current_swing: Dict, 
                                    flaw_analysis: Dict) -> Dict:
        """
        Get personalized coaching recommendations based on current swing
        and historical performance
        
        Args:
            user_id: User identifier
            current_swing: Current swing data with metrics
            flaw_analysis: Flaw analysis from FlawDetector
            
        Returns:
            Dictionary with recommendations, trends, and personalized tips
        """
        # Get user's historical data
        user_stats = self.swing_db.get_user_stats(user_id)
        recent_swings = self._get_recent_swings(user_id, limit=20)
        
        # Analyze trends
        trends = self._analyze_trends(recent_swings)
        
        # Get personalized recommendations
        recommendations = self._generate_recommendations(
            current_swing, flaw_analysis, trends, user_stats
        )
        
        # Track recommendation
        self.recommendation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'recommendations': len(recommendations),
            'top_priority': recommendations[0]['metric'] if recommendations else None
        })
        
        return {
            'recommendations': recommendations,
            'trends': trends,
            'user_stats': user_stats,
            'improvement_areas': self._identify_improvement_areas(trends, flaw_analysis),
            'encouragement': self._get_encouragement_message(trends, user_stats)
        }
    
    def _get_recent_swings(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get recent swings for a user"""
        sessions = self.swing_db.get_user_sessions(user_id, limit=10)
        swings = []
        for session in sessions:
            session_swings = self.swing_db.get_session_swings(session['session_id'])
            swings.extend(session_swings)
        
        # Sort by timestamp and limit
        swings.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return swings[:limit]
    
    def _analyze_trends(self, recent_swings: List[Dict]) -> Dict:
        """Analyze improvement trends from recent swings"""
        if len(recent_swings) < 5:
            return {'has_enough_data': False}
        
        # Group by metric
        metric_values = defaultdict(list)
        scores = []
        
        for swing in recent_swings:
            metrics = swing.get('metrics', {})
            overall_score = swing.get('overall_score', 0)
            scores.append(overall_score)
            
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    metric_values[metric].append(value)
        
        # Calculate trends
        trends = {'has_enough_data': True}
        
        # Overall score trend
        if len(scores) >= 10:
            recent_avg = sum(scores[:5]) / 5
            previous_avg = sum(scores[5:10]) / 5
            trends['overall_score_trend'] = {
                'recent_avg': recent_avg,
                'previous_avg': previous_avg,
                'improvement': recent_avg - previous_avg,
                'direction': 'improving' if recent_avg > previous_avg else 'declining'
            }
        
        # Metric trends
        for metric, values in metric_values.items():
            if len(values) >= 10:
                recent_avg = sum(values[:5]) / 5
                previous_avg = sum(values[5:10]) / 5
                trends[f'{metric}_trend'] = {
                    'recent_avg': recent_avg,
                    'previous_avg': previous_avg,
                    'change': recent_avg - previous_avg
                }
        
        return trends
    
    def _generate_recommendations(self, current_swing: Dict, flaw_analysis: Dict,
                                 trends: Dict, user_stats: Dict) -> List[Dict]:
        """Generate personalized coaching recommendations"""
        recommendations = []
        
        # Start with flaw-based recommendations
        flaws = flaw_analysis.get('flaws', [])
        for flaw in flaws[:3]:  # Top 3 flaws
            metric = flaw.get('metric')
            severity = flaw.get('severity', 0)
            
            # Check if this is a recurring issue
            is_recurring = self._is_recurring_issue(metric, trends)
            
            recommendation = {
                'metric': metric,
                'priority': 'high' if severity > 0.7 else 'medium' if severity > 0.4 else 'low',
                'severity': severity,
                'current_value': flaw.get('value'),
                'target_range': f"{flaw.get('ideal_min')}-{flaw.get('ideal_max')}",
                'recommendation': flaw.get('recommendation', ''),
                'is_recurring': is_recurring,
                'drill_suggestion': self._get_drill_suggestion(metric, severity)
            }
            recommendations.append(recommendation)
        
        # Add trend-based recommendations
        if trends.get('has_enough_data'):
            if trends.get('overall_score_trend', {}).get('direction') == 'declining':
                recommendations.append({
                    'metric': 'overall_performance',
                    'priority': 'medium',
                    'recommendation': 'Your recent scores have declined. Focus on fundamentals and consistency.',
                    'drill_suggestion': 'Practice tempo drills and balance exercises'
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))
        
        return recommendations
    
    def _is_recurring_issue(self, metric: str, trends: Dict) -> bool:
        """Check if a metric issue is recurring based on trends"""
        trend_key = f'{metric}_trend'
        if trend_key in trends:
            trend = trends[trend_key]
            # If consistently outside ideal range, it's recurring
            return abs(trend.get('change', 0)) < 0.1  # Little improvement
        return False
    
    def _get_drill_suggestion(self, metric: str, severity: float) -> str:
        """Get specific drill suggestion for a metric"""
        drills = {
            'hip_rotation_top': 'Hip rotation drill: Practice turning hips while keeping shoulders stable',
            'shoulder_rotation_top': 'Shoulder turn drill: Focus on full shoulder turn in backswing',
            'x_factor': 'X-factor drill: Increase separation between shoulders and hips at top',
            'spine_angle_address': 'Posture drill: Maintain consistent spine angle at address',
            'tempo_ratio': 'Tempo drill: Practice 3:1 backswing to downswing ratio',
            'weight_transfer': 'Weight shift drill: Practice transferring weight from back to front foot'
        }
        return drills.get(metric, 'General swing improvement drill')
    
    def _identify_improvement_areas(self, trends: Dict, flaw_analysis: Dict) -> List[str]:
        """Identify areas showing improvement"""
        improvement_areas = []
        
        if trends.get('has_enough_data'):
            for key, trend_data in trends.items():
                if key.endswith('_trend') and isinstance(trend_data, dict):
                    change = trend_data.get('change', 0)
                    if change > 0:  # Positive change
                        metric = key.replace('_trend', '')
                        improvement_areas.append(metric)
        
        return improvement_areas
    
    def _get_encouragement_message(self, trends: Dict, user_stats: Dict) -> str:
        """Get encouraging message based on performance"""
        if not trends.get('has_enough_data'):
            return "Keep practicing! More data will help track your improvement."
        
        overall_trend = trends.get('overall_score_trend', {})
        improvement = overall_trend.get('improvement', 0)
        
        if improvement > 5:
            return f"Excellent progress! Your scores improved by {improvement:.1f} points recently. Keep it up!"
        elif improvement > 0:
            return f"Great job! You're showing improvement. Keep focusing on consistency."
        elif improvement == 0:
            return "You're maintaining your performance. Try focusing on one specific area to break through."
        else:
            return "Don't get discouraged! Golf improvement takes time. Focus on fundamentals and stay consistent."
    
    def get_historical_insights(self, user_id: str, days: int = 30) -> Dict:
        """Get historical insights for a user over specified days"""
        sessions = self.swing_db.get_user_sessions(user_id, limit=100)
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s['start_time']) >= cutoff_date
        ]
        
        if not recent_sessions:
            return {'message': 'No recent sessions found'}
        
        # Analyze patterns
        total_swings = sum(len(self.swing_db.get_session_swings(s['session_id'])) 
                          for s in recent_sessions)
        
        return {
            'sessions_count': len(recent_sessions),
            'total_swings': total_swings,
            'average_per_session': total_swings / len(recent_sessions) if recent_sessions else 0,
            'most_active_day': self._get_most_active_day(recent_sessions),
            'recommendation': self._get_practice_recommendation(len(recent_sessions), total_swings)
        }
    
    def _get_most_active_day(self, sessions: List[Dict]) -> str:
        """Get the day of week with most practice"""
        day_counts = defaultdict(int)
        for session in sessions:
            date = datetime.fromisoformat(session['start_time'])
            day_counts[date.strftime('%A')] += 1
        
        if day_counts:
            return max(day_counts.items(), key=lambda x: x[1])[0]
        return "Unknown"
    
    def _get_practice_recommendation(self, session_count: int, total_swings: int) -> str:
        """Get recommendation based on practice frequency"""
        if session_count < 3:
            return "Try to practice at least 3 times per week for best results."
        elif total_swings < 20:
            return "Aim for at least 20 swings per session to see meaningful improvement."
        else:
            return "Great practice frequency! Keep up the consistent work."

