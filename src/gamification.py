"""
Gamification Module - Scoring system and achievements for practice sessions
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class GamificationSystem:
    """
    Gamification system for practice sessions
    Tracks achievements, scores, streaks, and provides motivation
    """
    
    def __init__(self, swing_db):
        """
        Initialize gamification system
        
        Args:
            swing_db: SwingDatabase instance
        """
        self.swing_db = swing_db
        self.achievements = self._load_achievements()
        logger.info("Gamification system initialized")
    
    def calculate_session_score(self, session_swings: List[Dict]) -> Dict:
        """
        Calculate overall score for a practice session
        
        Args:
            session_swings: List of swing data dictionaries
            
        Returns:
            Dictionary with session score, achievements, and stats
        """
        if not session_swings:
            return {'score': 0, 'achievements': [], 'stats': {}}
        
        # Calculate base score from swing quality
        total_score = 0
        swing_scores = []
        
        for swing in session_swings:
            swing_score = swing.get('overall_score', 0)
            swing_scores.append(swing_score)
            total_score += swing_score
        
        avg_score = total_score / len(session_swings) if session_swings else 0
        
        # Calculate consistency bonus
        if len(swing_scores) > 1:
            std_dev = self._calculate_std_dev(swing_scores)
            consistency_bonus = max(0, 10 - std_dev)  # Lower std dev = higher bonus
        else:
            consistency_bonus = 0
        
        # Calculate improvement bonus
        if len(swing_scores) >= 5:
            first_half = sum(swing_scores[:len(swing_scores)//2]) / (len(swing_scores)//2)
            second_half = sum(swing_scores[len(swing_scores)//2:]) / (len(swing_scores) - len(swing_scores)//2)
            improvement = second_half - first_half
            improvement_bonus = max(0, min(10, improvement))  # Cap at 10
        else:
            improvement_bonus = 0
        
        # Volume bonus
        volume_bonus = min(5, len(session_swings) / 10)  # 5 points for 50+ swings
        
        # Final session score
        session_score = avg_score + consistency_bonus + improvement_bonus + volume_bonus
        session_score = min(100, max(0, session_score))  # Clamp to 0-100
        
        # Check for achievements
        achievements = self._check_achievements(session_swings, session_score)
        
        return {
            'score': round(session_score, 1),
            'breakdown': {
                'average_swing_score': round(avg_score, 1),
                'consistency_bonus': round(consistency_bonus, 1),
                'improvement_bonus': round(improvement_bonus, 1),
                'volume_bonus': round(volume_bonus, 1)
            },
            'achievements': achievements,
            'stats': {
                'total_swings': len(session_swings),
                'best_swing': max(swing_scores) if swing_scores else 0,
                'worst_swing': min(swing_scores) if swing_scores else 0,
                'consistency': round(100 - self._calculate_std_dev(swing_scores), 1) if len(swing_scores) > 1 else 100
            }
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _check_achievements(self, session_swings: List[Dict], session_score: float) -> List[Dict]:
        """Check which achievements were unlocked this session"""
        achievements = []
        
        swing_count = len(session_swings)
        
        # Volume achievements
        if swing_count >= 50:
            achievements.append({
                'id': 'volume_master',
                'name': 'Volume Master',
                'description': 'Completed 50+ swings in a session',
                'points': 50
            })
        elif swing_count >= 25:
            achievements.append({
                'id': 'volume_enthusiast',
                'name': 'Volume Enthusiast',
                'description': 'Completed 25+ swings in a session',
                'points': 25
            })
        
        # Score achievements
        if session_score >= 90:
            achievements.append({
                'id': 'excellent_session',
                'name': 'Excellent Session',
                'description': 'Achieved 90+ session score',
                'points': 100
            })
        elif session_score >= 80:
            achievements.append({
                'id': 'great_session',
                'name': 'Great Session',
                'description': 'Achieved 80+ session score',
                'points': 50
            })
        
        # Consistency achievements
        if swing_count >= 10:
            swing_scores = [s.get('overall_score', 0) for s in session_swings]
            std_dev = self._calculate_std_dev(swing_scores)
            if std_dev < 5:
                achievements.append({
                    'id': 'consistency_king',
                    'name': 'Consistency King',
                    'description': 'Maintained very consistent swings (std dev < 5)',
                    'points': 75
                })
        
        # Improvement achievements
        if swing_count >= 10:
            first_half = sum(s.get('overall_score', 0) for s in session_swings[:swing_count//2]) / (swing_count//2)
            second_half = sum(s.get('overall_score', 0) for s in session_swings[swing_count//2:]) / (swing_count - swing_count//2)
            if second_half > first_half + 5:
                achievements.append({
                    'id': 'improvement_master',
                    'name': 'Improvement Master',
                    'description': 'Improved significantly during session',
                    'points': 50
                })
        
        return achievements
    
    def get_user_level(self, user_id: str) -> Dict:
        """Calculate user level based on total practice"""
        user_stats = self.swing_db.get_user_stats(user_id)
        total_swings = user_stats.get('total_swings', 0)
        total_sessions = user_stats.get('total_sessions', 0)
        
        # Calculate level (1 level per 100 swings)
        level = (total_swings // 100) + 1
        xp_current = total_swings % 100
        xp_needed = 100
        
        # Calculate rank
        if level >= 20:
            rank = "Master"
        elif level >= 15:
            rank = "Expert"
        elif level >= 10:
            rank = "Advanced"
        elif level >= 5:
            rank = "Intermediate"
        else:
            rank = "Beginner"
        
        return {
            'level': level,
            'rank': rank,
            'total_swings': total_swings,
            'total_sessions': total_sessions,
            'xp_current': xp_current,
            'xp_needed': xp_needed,
            'progress_percent': (xp_current / xp_needed) * 100 if xp_needed > 0 else 0
        }
    
    def get_streak_info(self, user_id: str) -> Dict:
        """Get practice streak information"""
        sessions = self.swing_db.get_user_sessions(user_id, limit=100)
        
        if not sessions:
            return {'current_streak': 0, 'longest_streak': 0, 'days': []}
        
        # Sort by date
        sessions.sort(key=lambda x: x['start_time'], reverse=True)
        
        # Calculate current streak
        current_streak = 0
        last_date = None
        
        for session in sessions:
            session_date = datetime.fromisoformat(session['start_time']).date()
            
            if last_date is None:
                last_date = session_date
                current_streak = 1
            else:
                days_diff = (last_date - session_date).days
                if days_diff == 1:  # Consecutive day
                    current_streak += 1
                    last_date = session_date
                elif days_diff == 0:  # Same day
                    continue
                else:
                    break
        
        # Calculate longest streak
        longest_streak = self._calculate_longest_streak(sessions)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_practice': sessions[0]['start_time'] if sessions else None
        }
    
    def _calculate_longest_streak(self, sessions: List[Dict]) -> int:
        """Calculate longest practice streak"""
        if not sessions:
            return 0
        
        dates = sorted(set(
            datetime.fromisoformat(s['start_time']).date() 
            for s in sessions
        ), reverse=True)
        
        if not dates:
            return 0
        
        longest = 1
        current = 1
        
        for i in range(1, len(dates)):
            days_diff = (dates[i-1] - dates[i]).days
            if days_diff == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        
        return longest
    
    def _load_achievements(self) -> List[Dict]:
        """Load achievement definitions"""
        return [
            {
                'id': 'first_swing',
                'name': 'First Swing',
                'description': 'Recorded your first swing',
                'points': 10
            },
            {
                'id': 'volume_enthusiast',
                'name': 'Volume Enthusiast',
                'description': 'Completed 25+ swings in a session',
                'points': 25
            },
            {
                'id': 'volume_master',
                'name': 'Volume Master',
                'description': 'Completed 50+ swings in a session',
                'points': 50
            },
            {
                'id': 'consistency_king',
                'name': 'Consistency King',
                'description': 'Maintained very consistent swings',
                'points': 75
            },
            {
                'id': 'improvement_master',
                'name': 'Improvement Master',
                'description': 'Improved significantly during session',
                'points': 50
            },
            {
                'id': 'excellent_session',
                'name': 'Excellent Session',
                'description': 'Achieved 90+ session score',
                'points': 100
            }
        ]

