"""
YouTubeDownloader - Utility to download videos from YouTube
Wraps the 'yt-dlp' library.
"""

import yt_dlp
import logging
import asyncio
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """
    A simple wrapper for yt-dlp to download videos for analysis.
    """

    def __init__(self, output_dir: str = "./data/pro_videos_raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def download_video(self, url: str, output_filename: Optional[str] = None) -> Optional[str]:
        """
        Downloads a single video from a YouTube URL.
        
        Args:
            url: The full YouTube URL.
            output_filename: Optional name for the file. 
                             If None, yt-dlp will auto-name it.

        Returns:
            The file path to the downloaded video, or None if download failed.
        """
        logger.info(f"Attempting to download video from: {url}")

        if not output_filename:
            # Use default yt-dlp naming
            output_template = str(self.output_dir / '%(title)s.%(ext)s')
        else:
            # Use specified filename
            output_template = str(self.output_dir / output_filename)

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'noplaylist': True,
            'quiet': True,
            'logger': logger,
        }

        try:
            # yt-dlp runs synchronously, so we run it in an executor
            # to avoid blocking the asyncio event loop.
            loop = asyncio.get_event_loop()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None,  # Use default ThreadPoolExecutor
                    lambda: ydl.extract_info(url, download=True)
                )
            
            # Get the actual path of the downloaded file
            downloaded_path = ydl.prepare_filename(info)
            
            if Path(downloaded_path).exists():
                logger.info(f"Successfully downloaded: {downloaded_path}")
                return downloaded_path
            else:
                logger.error("yt-dlp reported success but file not found.")
                return None

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            if "Unsupported URL" in str(e):
                logger.error("The URL may be invalid or private.")
            if "HTTP Error 404" in str(e):
                logger.error("Video not found (404).")
            return None
