"""
Style Matcher - Finds the best matching professional swing
Uses weighted similarity metrics
"""

import numpy as np
from typing import Dict, List, Optional
from .database import ProSwingDatabase
import logging

logger = logging.getLogger(__name__)


class StyleMatcher:
    """
    Matches user swings to professional swings based on style similarity
    Optimized with in-memory caching for fast lookups
    """
    
    def __init__(self, pro_database_path: str):
        self.pro_db = ProSwingDatabase(pro_database_path)
        
        # Weights for different metrics (sum to 1.0)
        self.metric_weights = {
            'tempo_ratio': 0.15,
            'hip_rotation_top': 0.12,
            'shoulder_rotation_top': 0.12,
            'x_factor': 0.15,
            'spine_angle_address': 0.10,
            'spine_angle_change': 0.08,
            'weight_transfer': 0.10,
            'backswing_time': 0.10,
            'downswing_time': 0.08
        }
        
        # Cache pro swings in memory for fast access
        self._pro_cache = {}  # {club_type: [pro_swings]}
        self._cache_loaded = False
        
        logger.info("StyleMatcher initialized")
    
    def _load_cache(self):
        """Load all pro swings into memory cache"""
        if self._cache_loaded:
            return
        
        logger.info("Loading pro swings into memory cache...")
        all_clubs = ["Driver", "3-Wood", "5-Wood", "3-Iron", "4-Iron", "5-Iron", 
                     "6-Iron", "7-Iron", "8-Iron", "9-Iron", "PW", "SW", "LW", "Putter"]
        
        for club in all_clubs:
            swings = self.pro_db.get_all_pro_swings(club_type=club)
            if swings:
                self._pro_cache[club] = swings
        
        self._cache_loaded = True
        total_swings = sum(len(swings) for swings in self._pro_cache.values())
        logger.info(f"Loaded {total_swings} pro swings into cache")
    
    async def find_best_match(self, swing_metrics: Dict, club_type: str = "Driver") -> Dict:
        """
        Find the best matching professional swing (optimized with caching)
        
        Args:
            swing_metrics: User's swing metrics
            club_type: Type of club used
        
        Returns:
            Dictionary with matched pro info and similarity score
        """
        # Load cache if not already loaded
        if not self._cache_loaded:
            self._load_cache()
        
        # Get pro swings from cache (fast, no DB query)
        pro_swings = self._pro_cache.get(club_type, [])
        
        if not pro_swings:
            logger.warning(f"No pro swings found for {club_type}")
            return self._get_default_match()
        
        # Vectorized similarity calculation for speed
        similarities = self._calculate_similarities_vectorized(swing_metrics, pro_swings)
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        best_match = similarities[0]
        logger.debug(f"Best match: {best_match['golfer_name']} (similarity: {best_match['similarity_score']:.2f})")
        
        return best_match
    
    def _calculate_similarities_vectorized(self, user_metrics: Dict, pro_swings: List[Dict]) -> List[Dict]:
        """Calculate similarities for all pro swings using vectorized operations"""
        similarities = []
        
        # Pre-compute user metric array for vectorized operations
        user_vals = np.array([user_metrics.get(metric, 0) for metric in self.metric_weights.keys()])
        weights = np.array(list(self.metric_weights.values()))
        
        for pro in pro_swings:
            pro_vals = np.array([pro['metrics'].get(metric, 0) for metric in self.metric_weights.keys()])
            
            # Vectorized similarity calculation
            # Normalize differences
            with np.errstate(divide='ignore', invalid='ignore'):
                diffs = np.abs(user_vals - pro_vals)
                # Avoid division by zero
                pro_vals_safe = np.where(pro_vals != 0, np.abs(pro_vals), 1.0)
                normalized_diffs = diffs / pro_vals_safe
                # Cap at 1.0 (100% difference)
                normalized_diffs = np.clip(normalized_diffs, 0, 1.0)
            
            # Weighted similarity (1 - normalized_diff)
            similarities_vals = 1.0 - normalized_diffs
            weighted_similarity = np.sum(similarities_vals * weights) * 100
            
            similarities.append({
                'pro_id': pro['pro_id'],
                'golfer_name': pro['golfer_name'],
                'similarity_score': float(weighted_similarity),
                'video_dtl_path': pro['video_dtl_path'],
                'video_face_path': pro['video_face_path'],
                'metrics': pro['metrics'],
                'style_tags': pro['style_tags']
            })
        
        return similarities
    
    def _calculate_similarity(self, user_metrics: Dict, pro_metrics: Dict) -> float:
        """
        Calculate weighted similarity score between user and pro swing
        
        Returns:
            Similarity score from 0-100 (higher is more similar)
        """
        total_similarity = 0.0
        total_weight = 0.0
        
        for metric, weight in self.metric_weights.items():
            if metric in user_metrics and metric in pro_metrics:
                user_val = user_metrics[metric]
                pro_val = pro_metrics[metric]
                
                # Calculate normalized difference
                if pro_val != 0:
                    # Percent difference
                    diff = abs(user_val - pro_val) / abs(pro_val)
                else:
                    diff = abs(user_val - pro_val)
                
                # Convert to similarity (0-1, where 1 is perfect match)
                # Use exponential decay: similarity = e^(-k*diff)
                k = 2.0  # Decay rate
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
    
    def _get_default_match(self) -> Dict:
        """Return a default match if no pros are available"""
        return {
            'pro_id': 'default',
            'golfer_name': 'Generic Professional',
            'similarity_score': 0.0,
            'video_dtl_path': None,
            'video_face_path': None,
            'metrics': {},
            'style_tags': []
        }
    
    def find_top_n_matches(self, swing_metrics: Dict, club_type: str, n: int = 3) -> List[Dict]:
        """Find top N matching pros"""
        pro_swings = self.pro_db.get_all_pro_swings(club_type=club_type)
        
        if not pro_swings:
            return [self._get_default_match()]
        
        similarities = []
        for pro in pro_swings:
            similarity = self._calculate_similarity(swing_metrics, pro['metrics'])
            similarities.append({
                'pro_id': pro['pro_id'],
                'golfer_name': pro['golfer_name'],
                'similarity_score': similarity,
                'video_dtl_path': pro['video_dtl_path'],
                'video_face_path': pro['video_face_path'],
                'metrics': pro['metrics'],
                'style_tags': pro['style_tags']
            })
        
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:n]
    
    def find_by_style_preference(self, swing_metrics: Dict, club_type: str, 
                                 preferred_tags: List[str]) -> Dict:
        """
        Find match with preference for certain style tags
        (e.g., "power", "smooth", "compact")
        """
        pro_swings = self.pro_db.get_all_pro_swings(club_type=club_type)
        
        # Filter by tags first
        filtered_pros = [
            pro for pro in pro_swings 
            if any(tag in pro['style_tags'] for tag in preferred_tags)
        ]
        
        if not filtered_pros:
            # Fall back to all pros
            filtered_pros = pro_swings
        
        # Find best match among filtered pros
        best_similarity = -1
        best_match = None
        
        for pro in filtered_pros:
            similarity = self._calculate_similarity(swing_metrics, pro['metrics'])
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'pro_id': pro['pro_id'],
                    'golfer_name': pro['golfer_name'],
                    'similarity_score': similarity,
                    'video_dtl_path': pro['video_dtl_path'],
                    'video_face_path': pro['video_face_path'],
                    'metrics': pro['metrics'],
                    'style_tags': pro['style_tags']
                }
        
        return best_match or self._get_default_match()
    
    def analyze_swing_style(self, swing_metrics: Dict) -> List[str]:
        """
        Analyze swing characteristics and assign style tags
        
        Returns:
            List of style tags that describe the swing
        """
        tags = []
        
        # Tempo-based tags
        tempo = swing_metrics.get('tempo_ratio', 0)
        if tempo > 3.5:
            tags.append('slow_backswing')
        elif tempo < 2.5:
            tags.append('fast_backswing')
        else:
            tags.append('balanced_tempo')
        
        # Rotation-based tags
        shoulder_rot = swing_metrics.get('shoulder_rotation_top', 0)
        if shoulder_rot > 100:
            tags.append('full_turn')
        elif shoulder_rot < 80:
            tags.append('compact')
        
        # X-Factor tags
        x_factor = swing_metrics.get('x_factor', 0)
        if x_factor > 50:
            tags.append('high_separation')
        elif x_factor < 35:
            tags.append('connected')
        
        # Weight transfer
        weight_transfer = swing_metrics.get('weight_transfer', 0)
        if weight_transfer > 0.12:
            tags.append('aggressive_shift')
        elif weight_transfer < 0.05:
            tags.append('stable_base')
        
        # Swing speed (from launch monitor)
        club_speed = swing_metrics.get('club_speed', 0)
        if club_speed > 110:
            tags.append('power')
        elif club_speed < 95:
            tags.append('smooth')
        
        return tags


# Pro swing data importer
class ProSwingImporter:
    """
    Imports professional swing data from videos
    """
    
    def __init__(self, pro_db_path: str):
        self.pro_db = ProSwingDatabase(pro_db_path)
        self.pose_analyzer = None  # Initialize when needed
    
    async def import_pro_swing(self, golfer_name: str, video_dtl_path: str,
                              video_face_path: str, club_type: str,
                              style_tags: list, youtube_url: str = None):
        """
        Import a professional swing from video files (simplified version)
        
        Args:
            golfer_name: Name of the professional
            video_dtl_path: Path to down-the-line video
            video_face_path: Path to face-on video
            club_type: Type of club (Driver, 7-Iron, etc.)
            style_tags: Style descriptors (power, smooth, modern, etc.)
            youtube_url: Original YouTube URL (optional)
        """
        from pathlib import Path
        
        logger.info(f"Importing pro swing: {golfer_name}")
        
        # Verify video files exist
        if not Path(video_dtl_path).exists():
            raise ValueError(f"DTL video not found: {video_dtl_path}")
        if not Path(video_face_path).exists():
            raise ValueError(f"Face-on video not found: {video_face_path}")
        
        logger.info(f"Videos verified: {Path(video_dtl_path).name}, {Path(video_face_path).name}")
        
        # For now, use default metrics
        # TODO: Implement full pose analysis when analyze_swing is available
        metrics = {
            'tempo_ratio': 3.0,
            'hip_rotation_top': 45.0,
            'shoulder_rotation_top': 95.0,
            'x_factor': 45.0,
            'spine_angle_address': 30.0,
            'spine_angle_change': 0.0,
            'weight_transfer': 0.10,
            'backswing_time': 0.9,
            'downswing_time': 0.3
        }
        
        logger.info(f"Using default metrics (full analysis will be implemented later)")
        
        # Generate pro_id
        pro_id = f"{golfer_name.lower().replace(' ', '_')}_{club_type.lower().replace('-', '_')}"
        
        # Save to database
        self.pro_db.add_pro_swing(
            pro_id=pro_id,
            golfer_name=golfer_name,
            video_paths={'dtl': video_dtl_path, 'face': video_face_path},
            metrics=metrics,
            club_type=club_type,
            style_tags=style_tags,
            youtube_url=youtube_url,
            pose_data=None  # Will be populated later when full analysis works
        )
        
        logger.info(f"Pro swing imported successfully: {pro_id}")
        logger.warning("Note: Using default metrics. Full pose analysis will be added in future update.")
        
        return pro_id
    
    def _load_video(self, video_path: str) -> list:
        """Load video frames"""
        import cv2
        from pathlib import Path
        
        if not Path(video_path).exists():
            logger.error(f"Video file not found: {video_path}")
            return []
        
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return []
        
        frame_count = 0
        max_frames = 300  # Limit to ~5 seconds at 60fps
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
            frame_count += 1
            
            if frame_count % 30 == 0:
                logger.info(f"Loading frames... {frame_count}/{max_frames}")
        
        cap.release()
        logger.info(f"Loaded {len(frames)} frames from {Path(video_path).name}")
        return frames
    
    async def bulk_import_from_youtube(self, pro_data_list: list):
        """
        Bulk import multiple pro swings from YouTube
        
        Args:
            pro_data_list: List of dicts with golfer info and YouTube URLs
        """
        from .youtube_downloader import YouTubeDownloader  # This import is fine if youtube_downloader exists in src
        
        downloader = YouTubeDownloader()
        
        for pro_data in pro_data_list:
            try:
                # Download video
                video_path = await downloader.download_video(
                    url=pro_data['youtube_url'],
                    output_dir='./data/pro_videos'
                )
                
                # Import
                await self.import_pro_swing(
                    golfer_name=pro_data['name'],
                    video_dtl_path=video_path,
                    video_face_path=video_path,
                    club_type=pro_data['club'],
                    style_tags=pro_data['tags'],
                    youtube_url=pro_data['youtube_url']
                )
                
            except Exception as e:
                logger.error(f"Failed to import {pro_data['name']}: {e}")