"""
Pro Swing Importer - Import professional swings into database
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.style_matcher import ProSwingImporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def import_swing_interactive():
    """Interactive CLI for importing pro swings"""
    
    print("="*60)
    print("Pro Swing Importer")
    print("="*60)
    print()
    
    # Initialize importer
    importer = ProSwingImporter('./data/pro_swings.db')
    
    # Get golfer name
    golfer_name = input("Golfer name (e.g., 'Justin Thomas'): ").strip()
    
    # Get video paths
    print("\nVideo files:")
    dtl_path = input("  DTL video path: ").strip()
    face_path = input("  Face-on video path (press Enter if same as DTL): ").strip()
    
    if not face_path:
        face_path = dtl_path
    
    # Validate paths
    if not Path(dtl_path).exists():
        print(f"\nERROR: DTL video not found: {dtl_path}")
        return
    
    if not Path(face_path).exists():
        print(f"\nERROR: Face-on video not found: {face_path}")
        return
    
    # Get club type
    print("\nClub types:")
    print("  1. Driver")
    print("  2. 3-Wood")
    print("  3. 5-Iron")
    print("  4. 7-Iron")
    print("  5. Wedge")
    club_choice = input("Select club (1-5): ").strip()
    
    club_map = {
        '1': 'Driver',
        '2': '3-Wood',
        '3': '5-Iron',
        '4': '7-Iron',
        '5': 'Wedge'
    }
    club_type = club_map.get(club_choice, 'Driver')
    
    # Get style tags
    print("\nStyle tags (comma-separated):")
    print("  Examples: power, smooth, compact, athletic, modern, classic")
    tags_input = input("Tags: ").strip()
    style_tags = [t.strip() for t in tags_input.split(',') if t.strip()]
    
    if not style_tags:
        style_tags = ['modern']
    
    # YouTube URL (optional)
    youtube_url = input("\nYouTube URL (optional, press Enter to skip): ").strip()
    if not youtube_url:
        youtube_url = None
    
    # Confirm
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Golfer: {golfer_name}")
    print(f"DTL video: {dtl_path}")
    print(f"Face-on video: {face_path}")
    print(f"Club: {club_type}")
    print(f"Style tags: {', '.join(style_tags)}")
    if youtube_url:
        print(f"YouTube: {youtube_url}")
    print("="*60)
    
    confirm = input("\nProceed with import? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Import cancelled.")
        return
    
    # Import
    print("\nImporting... This may take a few minutes.")
    print("(Processing video and analyzing swing)")
    
    try:
        pro_id = await importer.import_pro_swing(
            golfer_name=golfer_name,
            video_dtl_path=dtl_path,
            video_face_path=face_path,
            club_type=club_type,
            style_tags=style_tags,
            youtube_url=youtube_url
        )
        
        print("\n" + "="*60)
        print("IMPORT SUCCESSFUL!")
        print("="*60)
        print(f"Pro ID: {pro_id}")
        print(f"Added to database: ./data/pro_swings.db")
        print("="*60)
        
    except Exception as e:
        print(f"\nERROR: Import failed: {e}")
        logger.error("Import error", exc_info=True)


async def import_quick(golfer_name: str, video_path: str, club_type: str = "Driver"):
    """Quick import for command-line use"""
    
    importer = ProSwingImporter('./data/pro_swings.db')
    
    # Auto-detect style tags based on name
    style_tags = ['modern']
    
    pro_id = await importer.import_pro_swing(
        golfer_name=golfer_name,
        video_dtl_path=video_path,
        video_face_path=video_path,
        club_type=club_type,
        style_tags=style_tags,
        youtube_url=None
    )
    
    print(f"Imported {golfer_name} - ID: {pro_id}")


def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        # Quick mode: python import_pro_swing.py "Justin Thomas" "path/to/video.mp4" "Driver"
        golfer = sys.argv[1]
        video = sys.argv[2]
        club = sys.argv[3] if len(sys.argv) > 3 else "Driver"
        
        asyncio.run(import_quick(golfer, video, club))
    else:
        # Interactive mode
        asyncio.run(import_swing_interactive())


if __name__ == "__main__":
    main()