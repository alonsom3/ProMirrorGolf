"""
Pro Swing Style Matcher
Finds the best matching professional swing based on biomechanical similarity
"""

import numpy as np
import logging
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class StyleMatcher:
    """
    Matches user swings to professional swings using weighted feature comparison.
    Uses cosine similarity on normalized feature vectors.
    """
    
    def __init__(self, pro_db_path: str):
        # Import here to avoid circular imports
        from promirror.database.pro_db import ProSwingDatabase
        
        self.pro_db = ProSwingDatabase(pro_db_path)
        
        # Feature weights (must sum to 1.0)
        # These determine importance of each metric in matching
        self.metric_weights = {
            'tempo_ratio': 0.15,          # Backswing:downswing ratio
            'hip_rotation': 0.12,         # Hip turn at top
            'shoulder_rotation': 0.12,    # Shoulder turn at top
            'x_factor': 0.15,             # Shoulder-hip separation
            'spine_angle': 0.10,          # Forward tilt
            'weight_transfer': 0.10,      # Lateral weight shift
            'backswing_time': 0.10,       # Time to top of backswing
            'club_speed': 0.16            # Club head speed
        }
        
        logger.info("StyleMatcher initialized")
    
    async def find_best_match(self, user_metrics: Dict, club_type: str = "Driver") -> Dict:
        """
        Find the professional swing that most closely matches the user's swing.
        
        Args:
            user_metrics: Dictionary of user's swing metrics
            club_type: Type of club (Driver, 7-Iron, etc.)
            
        Returns:
            Dictionary containing:
                - pro_id: Unique identifier
                - golfer_name: Pro's name
                - similarity_score: 0-100 score
                - metrics: Pro's metrics
                - video_path: Path to pro's video
                - recommendations: Differences to work on
        """
        logger.info(f"Finding best pro match for {club_type} swing...")
        
        # Get all pros for this club type
        pros = self.pro_db.get_all_pros(club_type=club_type)
        
        if not pros:
            logger.warning(f"No pro swings found for {club_type}")
            return self._get_default_match()
        
        # Calculate similarity with each pro
        matches = []
        for pro in pros:
            similarity = self._calculate_similarity(user_metrics, pro['metrics'])
            
            matches.append({
                'pro_id': pro['pro_id'],
                'golfer_name': pro['golfer_name'],
                'similarity_score': similarity,
                'metrics': pro['metrics'],
                'video_path': pro.get('video_path'),
                'style_tags': pro.get('style_tags', [])
            })
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        best_match = matches[0]
        
        # Add specific recommendations
        best_match['recommendations'] = self._generate_recommendations(
            user_metrics, best_match['metrics']
        )
        
        logger.info(f"Best match: {best_match['golfer_name']} "
                   f"(similarity: {best_match['similarity_score']:.1f}%)")
        
        return best_match
    
    def _calculate_similarity(self, user_metrics: Dict, pro_metrics: Dict) -> float:
        """
        Calculate weighted similarity score between user and pro.
        Uses exponential decay: similarity = exp(-k * normalized_difference)
        
        Returns:
            Similarity score from 0-100 (100 = perfect match)
        """
        total_similarity = 0.0
        total_weight = 0.0
        
        for metric, weight in self.metric_weights.items():
            # Skip if either side missing this metric
            if metric not in user_metrics or metric not in pro_metrics:
                continue
            
            user_val = user_metrics[metric]
            pro_val = pro_metrics[metric]
            
            # Calculate normalized difference
            if pro_val != 0:
                diff = abs(user_val - pro_val) / abs(pro_val)
            else:
                diff = abs(user_val - pro_val)
            
            # Convert to similarity using exponential decay
            # k=2.0 means 50% similarity at ~35% difference
            k = 2.0
            similarity = np.exp(-k * diff)
            
            # Weight and accumulate
            total_similarity += similarity * weight
            total_weight += weight
        
        # Normalize to 0-100 scale
        if total_weight > 0:
            final_score = (total_similarity / total_weight) * 100
        else:
            final_score = 0.0
        
        return round(final_score, 2)
    
    def _generate_recommendations(self, user_metrics: Dict, pro_metrics: Dict) -> List[Dict]:
        """
        Generate specific recommendations based on differences from pro.
        
        Returns:
            List of recommendations with metric, difference, and advice
        """
        recommendations = []
        
        # Check each metric
        for metric in self.metric_weights.keys():
            if metric not in user_metrics or metric not in pro_metrics:
                continue
            
            user_val = user_metrics[metric]
            pro_val = pro_metrics[metric]
            diff = user_val - pro_val
            
            # Only recommend if difference > 10%
            if abs(diff) > abs(pro_val * 0.1):
                recommendations.append({
                    'metric': metric,
                    'your_value': user_val,
                    'pro_value': pro_val,
                    'difference': diff,
                    'advice': self._get_advice(metric, diff)
                })
        
        # Sort by absolute difference (most important first)
        recommendations.sort(key=lambda x: abs(x['difference']), reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _get_advice(self, metric: str, diff: float) -> str:
        """Get specific advice for improving a metric"""
        advice_map = {
            'hip_rotation': {
                'low': "Increase hip turn in backswing. Focus on rotating around your spine.",
                'high': "You may be overrotating your hips. Work on more upper body turn instead."
            },
            'shoulder_rotation': {
                'low': "Turn shoulders more fully. Try to get your back facing the target.",
                'high': "Your shoulder turn is very full. Make sure you maintain balance."
            },
            'x_factor': {
                'low': "Create more separation between shoulders and hips. Resist with lower body.",
                'high': "You have good separation. Focus on maintaining it through transition."
            },
            'spine_angle': {
                'low': "Increase forward tilt at address. Bend more from your hips.",
                'high': "You may be bent over too much. Stand a bit taller at address."
            },
            'weight_transfer': {
                'low': "Shift weight more to front foot through impact. Feel pressure on left side.",
                'high': "You're shifting a lot. Make sure it's controlled and not sliding."
            },
            'tempo_ratio': {
                'low': "Slow down your backswing relative to downswing. Try 3:1 tempo.",
                'high': "Your backswing is very slow. Speed it up slightly for better rhythm."
            },
            'club_speed': {
                'low': "Work on generating more speed. Focus on hip rotation and wrist lag.",
                'high': "Great speed! Make sure you're maintaining control and accuracy."
            }
        }
        
        direction = 'low' if diff < 0 else 'high'
        return advice_map.get(metric, {}).get(direction, "Work with a coach on this aspect.")
    
    def _get_default_match(self) -> Dict:
        """Return default match when no pros available"""
        return {
            'pro_id': 'default',
            'golfer_name': 'Generic Professional',
            'similarity_score': 0.0,
            'metrics': {},
            'video_path': None,
            'style_tags': [],
            'recommendations': []
        }
    
    def find_top_n_matches(self, user_metrics: Dict, club_type: str, n: int = 3) -> List[Dict]:
        """
        Find the top N matching pros.
        Useful for showing multiple comparison options.
        """
        pros = self.pro_db.get_all_pros(club_type=club_type)
        
        if not pros:
            return [self._get_default_match()]
        
        matches = []
        for pro in pros:
            similarity = self._calculate_similarity(user_metrics, pro['metrics'])
            matches.append({
                'pro_id': pro['pro_id'],
                'golfer_name': pro['golfer_name'],
                'similarity_score': similarity,
                'metrics': pro['metrics'],
                'video_path': pro.get('video_path'),
                'style_tags': pro.get('style_tags', [])
            })
        
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        return matches[:n]
    
    def analyze_swing_style(self, metrics: Dict) -> List[str]:
        """
        Analyze swing characteristics and assign style tags.
        
        Returns:
            List of style descriptors (e.g., ['power', 'fast_tempo', 'full_turn'])
        """
        tags = []
        
        # Tempo analysis
        tempo = metrics.get('tempo_ratio', 0)
        if tempo > 3.5:
            tags.append('slow_backswing')
        elif tempo < 2.5:
            tags.append('fast_backswing')
        else:
            tags.append('balanced_tempo')
        
        # Rotation analysis
        shoulder_rot = metrics.get('shoulder_rotation', 0)
        if shoulder_rot > 100:
            tags.append('full_turn')
        elif shoulder_rot < 80:
            tags.append('compact')
        
        # X-Factor analysis
        x_factor = metrics.get('x_factor', 0)
        if x_factor > 50:
            tags.append('high_separation')
        elif x_factor < 35:
            tags.append('connected')
        
        # Speed analysis
        club_speed = metrics.get('club_speed', 0)
        if club_speed > 110:
            tags.append('power')
        elif club_speed < 95:
            tags.append('smooth')
        
        # Weight transfer
        transfer = metrics.get('weight_transfer', 0)
        if transfer > 0.12:
            tags.append('aggressive_shift')
        elif transfer < 0.05:
            tags.append('stable_base')
        
        return tags


# Test function
def test_style_matcher():
    """Test the style matcher"""
    import asyncio
    
    async def run_test():
        # Sample user metrics
        user_metrics = {
            'hip_rotation': 42,
            'shoulder_rotation': 95,
            'x_factor': 48,
            'spine_angle': 32,
            'weight_transfer': 0.09,
            'tempo_ratio': 3.0,
            'backswing_time': 0.85,
            'club_speed': 105
        }
        
        # Initialize matcher
        matcher = StyleMatcher('./data/pro_swings.db')
        
        # Find best match
        match = await matcher.find_best_match(user_metrics, 'Driver')
        
        print(f"\n{'='*60}")
        print(f"Best Match: {match['golfer_name']}")
        print(f"Similarity: {match['similarity_score']:.1f}%")
        print(f"{'='*60}\n")
        
        print("Top Recommendations:")
        for i, rec in enumerate(match['recommendations'], 1):
            print(f"{i}. {rec['metric'].replace('_', ' ').title()}")
            print(f"   Your value: {rec['your_value']:.2f}")
            print(f"   Pro value: {rec['pro_value']:.2f}")
            print(f"   Advice: {rec['advice']}")
            print()
        
        # Analyze swing style
        style_tags = matcher.analyze_swing_style(user_metrics)
        print(f"Your swing style: {', '.join(style_tags)}")
    
    asyncio.run(run_test())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_style_matcher()
