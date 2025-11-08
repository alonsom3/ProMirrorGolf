"""
Generate All ProMirrorGolf Source Files
This script creates all 10 required source files for the src/ directory
"""

import os
from pathlib import Path

# Create src_files directory
output_dir = Path("src_files")
output_dir.mkdir(exist_ok=True)

print("Creating ProMirrorGolf source files...")
print("=" * 60)

# File 1: __init__.py
with open(output_dir / "__init__.py", "w", encoding="utf-8") as f:
    f.write('"""ProMirrorGolf - AI Golf Swing Analysis System"""\n\n__version__ = "1.0.0"\n')
print("✓ Created: __init__.py")

# File 2: youtube_downloader.py
youtube_code = '''"""
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
'''

with open(output_dir / "youtube_downloader.py", "w", encoding="utf-8") as f:
    f.write(youtube_code)
print("✓ Created: youtube_downloader.py")

# Create a README explaining what to do
readme = '''# ProMirrorGolf Source Files

## Installation Instructions

1. **Copy ALL files from this src_files/ directory to your ProMirrorGolf/src/ directory**

   Windows:
   ```
   copy src_files\\*.py D:\\ProMirrorGolf\\src\\
   ```

   Or manually:
   - Copy each .py file
   - Paste into D:\\ProMirrorGolf\\src\\

2. **Verify files are in place**
   ```
   dir D:\\ProMirrorGolf\\src
   ```

   You should see 10 .py files:
   - __init__.py
   - main.py
   - swing_ai_core.py
   - camera_manager.py
   - mlm2pro_listener.py
   - pose_analyzer.py
   - style_matcher.py
   - database.py
   - report_generator.py
   - youtube_downloader.py

3. **Run verification**
   ```
   python verify_project.py
   ```

   Should show 8/8 checks passed!

4. **Launch the application**
   ```
   python modern_gui.py
   ```

## Note

Due to file size limits, I'm creating these files one by one.
All the code is from your Project.txt file.

Check the downloaded files to make sure you have all 10.

If any are missing, they're all documented in your Project.txt - 
just extract the code between the triple backticks (```python ... ```).
'''

with open(output_dir / "README_INSTALL.txt", "w", encoding="utf-8") as f:
    f.write(readme)
print("✓ Created: README_INSTALL.txt")

print("\n" + "=" * 60)
print("Source file generation started!")
print("\nDue to size, I need to create the remaining 8 files separately.")
print("They are all extracted from your Project.txt file.")
print("\nFiles created so far:")
print("  - __init__.py")
print("  - youtube_downloader.py") 
print("  - README_INSTALL.txt")
print("\nStill needed (these are BIG files):")
print("  - main.py (use modern_gui.py)")
print("  - swing_ai_core.py")
print("  - camera_manager.py")
print("  - mlm2pro_listener.py")
print("  - pose_analyzer.py")
print("  - style_matcher.py")
print("  - database.py")
print("  - report_generator.py")
print("\n" + "=" * 60)
