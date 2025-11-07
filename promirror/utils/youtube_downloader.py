"""
YouTubeDownloader - Utility to download videos from YouTube
Wraps the 'yt-dlp' library for pro swing video collection
"""

import yt_dlp
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """
    Downloads golf swing videos from YouTube for pro database building.
    Uses yt-dlp for reliable, high-quality downloads.
    """
    
    def __init__(self, output_dir: str = "./data/pro_videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"YouTubeDownloader initialized: {output_dir}")
    
    async def download_video(self, url: str, output_filename: Optional[str] = None) -> Optional[str]:
        """
        Download a single video from YouTube.
        
        Args:
            url: Full YouTube URL
            output_filename: Optional custom filename (without extension)
        
        Returns:
            Path to downloaded file, or None if failed
        """
        logger.info(f"Downloading video from: {url}")
        
        if output_filename:
            output_template = str(self.output_dir / f"{output_filename}.%(ext)s")
        else:
            output_template = str(self.output_dir / "%(title)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
        }
        
        try:
            # Run yt-dlp in executor to avoid blocking async loop
            loop = asyncio.get_event_loop()
            
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info)
            
            downloaded_path = await loop.run_in_executor(None, download)
            
            if Path(downloaded_path).exists():
                logger.info(f"Successfully downloaded: {downloaded_path}")
                return downloaded_path
            else:
                logger.error("Download reported success but file not found")
                return None
                
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return None
    
    async def download_multiple(self, urls: List[str]) -> Dict[str, Optional[str]]:
        """
        Download multiple videos.
        
        Args:
            urls: List of YouTube URLs
        
        Returns:
            Dictionary mapping URLs to downloaded file paths
        """
        results = {}
        
        for url in urls:
            path = await self.download_video(url)
            results[url] = path
            
            # Small delay between downloads to be respectful
            await asyncio.sleep(2)
        
        success_count = sum(1 for p in results.values() if p is not None)
        logger.info(f"Downloaded {success_count}/{len(urls)} videos successfully")
        
        return results
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video information without downloading.
        Useful for validating URLs and checking video details.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'upload_date': info.get('upload_date'),
                }
        except Exception as e:
            logger.error(f"Failed to get info for {url}: {e}")
            return None


# Utility function for quick downloads
async def quick_download(url: str, output_dir: str = "./data/pro_videos") -> Optional[str]:
    """
    Quick download helper function.
    
    Usage:
        path = await quick_download("https://youtube.com/watch?v=...")
    """
    downloader = YouTubeDownloader(output_dir)
    return await downloader.download_video(url)


# Test function
async def test_downloader():
    """Test the downloader with a sample video"""
    downloader = YouTubeDownloader("./test_downloads")
    
    # Test URL (replace with actual golf swing video)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Sample URL
    
    print("Testing YouTube downloader...")
    print(f"Attempting to download: {test_url}")
    
    result = await downloader.download_video(test_url)
    
    if result:
        print(f"✅ Download successful: {result}")
    else:
        print("❌ Download failed")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_downloader())
