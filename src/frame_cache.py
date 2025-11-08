"""
Frame Cache - LRU cache for processed frames to avoid re-processing
"""

import logging
from typing import Dict, Optional
from collections import OrderedDict
import pickle
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class FrameCache:
    """
    LRU cache for processed frame data (pose landmarks, metrics)
    Reduces re-processing time for playback and comparison views
    """
    
    def __init__(self, max_size: int = 1000, cache_dir: Optional[Path] = None):
        """
        Initialize frame cache
        
        Args:
            max_size: Maximum number of frames to cache in memory
            cache_dir: Optional directory to persist cache to disk
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()  # LRU ordered dict
        self.cache_dir = cache_dir or Path("./data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, video_id: str, frame_index: int) -> str:
        """Create cache key from video ID and frame index"""
        return f"{video_id}_{frame_index}"
    
    def get(self, video_id: str, frame_index: int) -> Optional[Dict]:
        """
        Get cached frame data
        
        Args:
            video_id: Unique identifier for the video
            frame_index: Frame index within the video
            
        Returns:
            Cached pose data dictionary or None if not found
        """
        key = self._make_key(video_id, frame_index)
        
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        
        # Try to load from disk cache
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                # Add to memory cache
                self.set(video_id, frame_index, data)
                self.hits += 1
                return data
            except Exception as e:
                logger.warning(f"Failed to load cache from disk: {e}")
        
        self.misses += 1
        return None
    
    def set(self, video_id: str, frame_index: int, pose_data: Dict):
        """
        Cache frame data
        
        Args:
            video_id: Unique identifier for the video
            frame_index: Frame index within the video
            pose_data: Pose data dictionary to cache
        """
        key = self._make_key(video_id, frame_index)
        
        # Remove oldest entry if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key, _ = self.cache.popitem(last=False)
            # Optionally remove from disk
            cache_file = self.cache_dir / f"{oldest_key}.pkl"
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except:
                    pass
        
        # Add to cache (moves to end if already exists)
        self.cache[key] = pose_data
        self.cache.move_to_end(key)
        
        # Optionally save to disk for persistence
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(pose_data, f)
        except Exception as e:
            logger.debug(f"Failed to save cache to disk: {e}")
    
    def clear(self, video_id: Optional[str] = None):
        """
        Clear cache entries
        
        Args:
            video_id: If provided, clear only entries for this video. Otherwise clear all.
        """
        if video_id:
            # Clear entries for specific video
            keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{video_id}_")]
            for key in keys_to_remove:
                self.cache.pop(key, None)
                cache_file = self.cache_dir / f"{key}.pkl"
                if cache_file.exists():
                    try:
                        cache_file.unlink()
                    except:
                        pass
        else:
            # Clear all
            self.cache.clear()
            # Clear disk cache
            if self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("*.pkl"):
                    try:
                        cache_file.unlink()
                    except:
                        pass
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "total_requests": total
        }
    
    def invalidate_video(self, video_id: str):
        """Invalidate all cache entries for a specific video"""
        self.clear(video_id)

