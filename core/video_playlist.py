"""Video playlist creation and management."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PlaylistItem:
    """A single item in a video playlist."""
    shot_id: int
    video_path: str
    title: str
    duration: Optional[float] = None
    thumbnail_path: Optional[str] = None


@dataclass
class VideoPlaylist:
    """A video playlist containing multiple shots."""
    name: str
    description: str = ""
    items: list[PlaylistItem] = None
    created_at: str = ""
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if not self.created_at:
            from datetime import datetime
            self.created_at = datetime.now().isoformat()


class PlaylistManager:
    """Manages video playlists."""
    
    def __init__(self, playlists_file: Path) -> None:
        """Initialize playlist manager.
        
        Args:
            playlists_file: Path to JSON file storing playlists
        """
        self.playlists_file = playlists_file
        self.playlists: list[VideoPlaylist] = []
        self._load_playlists()
    
    def _load_playlists(self) -> None:
        """Load playlists from file."""
        if not self.playlists_file.exists():
            return
        
        try:
            with open(self.playlists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.playlists = [VideoPlaylist(**p) for p in data]
        except Exception as e:
            logger.error("Error loading playlists: %s", e, exc_info=True)
            self.playlists = []
    
    def _save_playlists(self) -> None:
        """Save playlists to file."""
        try:
            self.playlists_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.playlists_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(p) for p in self.playlists], f, indent=2)
        except Exception as e:
            logger.error("Error saving playlists: %s", e, exc_info=True)
    
    def create_playlist(self, name: str, description: str = "") -> VideoPlaylist:
        """Create a new playlist.
        
        Args:
            name: Playlist name
            description: Playlist description
            
        Returns:
            Created playlist
        """
        playlist = VideoPlaylist(name=name, description=description)
        self.playlists.append(playlist)
        self._save_playlists()
        return playlist
    
    def add_to_playlist(self, playlist_name: str, item: PlaylistItem) -> bool:
        """Add an item to a playlist.
        
        Args:
            playlist_name: Name of playlist
            item: Item to add
            
        Returns:
            True if successful
        """
        playlist = self.get_playlist(playlist_name)
        if not playlist:
            return False
        
        playlist.items.append(item)
        self._save_playlists()
        return True
    
    def get_playlist(self, name: str) -> Optional[VideoPlaylist]:
        """Get a playlist by name.
        
        Args:
            name: Playlist name
            
        Returns:
            Playlist or None if not found
        """
        for playlist in self.playlists:
            if playlist.name == name:
                return playlist
        return None
    
    def get_all_playlists(self) -> list[VideoPlaylist]:
        """Get all playlists."""
        return self.playlists.copy()
    
    def delete_playlist(self, name: str) -> bool:
        """Delete a playlist.
        
        Args:
            name: Playlist name
            
        Returns:
            True if successful
        """
        for i, playlist in enumerate(self.playlists):
            if playlist.name == name:
                self.playlists.pop(i)
                self._save_playlists()
                return True
        return False
    
    def export_playlist_m3u(self, playlist_name: str, output_path: Path) -> bool:
        """Export playlist to M3U format.
        
        Args:
            playlist_name: Name of playlist
            output_path: Path to output M3U file
            
        Returns:
            True if successful
        """
        playlist = self.get_playlist(playlist_name)
        if not playlist:
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for item in playlist.items:
                    f.write(f"#EXTINF:-1,{item.title}\n")
                    f.write(f"{item.video_path}\n")
            return True
        except Exception as e:
            logger.error("Error exporting playlist: %s", e, exc_info=True)
            return False

