"""
Pro Database Builder - Interactive Tool
Helps you populate the professional swing database
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from promirror.database.pro_db import ProSwingDatabase, create_sample_pro_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_header():
    """Print welcome header"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║              ProMirrorGolf Database Builder                ║
║                                                            ║
║  Build your professional swing database for comparison     ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)


def check_database_status():
    """Check current database status"""
    db_path = './data/pro_swings.db'
    
    print("\n" + "="*60)
    print("DATABASE STATUS")
    print("="*60)
    
    if not Path(db_path).exists():
        print(f"\n❌ Database not found at: {db_path}")
        print("   You need to build the database first.\n")
        return False
    
    try:
        db = ProSwingDatabase(db_path)
        stats = db.get_database_stats()
        
        print(f"\n✅ Database found: {db_path}")
        print(f"\n📊 Statistics:")
        print(f"   Total swings: {stats['total_swings']}")
        print(f"   Unique golfers: {stats['unique_golfers']}")
        
        if stats['by_club_type']:
            print(f"\n📋 By Club Type:")
            for club, count in stats['by_club_type'].items():
                print(f"   {club}: {count} swing(s)")
        
        if stats['total_swings'] > 0:
            print(f"\n🏌️ Golfers in database:")
            for name in db.list_all_golfers():
                print(f"   - {name}")
        else:
            print("\n⚠️  Database is empty!")
            print("   Import some pro swings to use the system.")
        
        db.close()
        return stats['total_swings'] > 0
        
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        return False


def add_sample_pros():
    """Add sample pro swings to database"""
    print("\n" + "="*60)
    print("ADDING SAMPLE PROFESSIONAL SWINGS")
    print("="*60)
    print("\nThis will add 3 sample pro swings:")
    print("  1. Rory McIlroy (Driver)")
    print("  2. Adam Scott (Driver)")
    print("  3. Tiger Woods (Driver)")
    print()
    
    confirm = input("Continue? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    try:
        db = ProSwingDatabase('./data/pro_swings.db')
        
        # Get sample pro data
        sample_pros = create_sample_pro_data()
        
        print("\nAdding pros...")
        for pro_data in sample_pros:
            db.add_pro_swing(**pro_data)
            print(f"  ✓ Added: {pro_data['golfer_name']}")
        
        db.close()
        
        print("\n✅ Sample pros added successfully!")
        print("\nYour database now has 3 pro swings for testing.")
        print("You can now run the main system to analyze your swings!\n")
        
    except Exception as e:
        print(f"\n❌ Error adding sample pros: {e}")
        import traceback
        traceback.print_exc()


def add_custom_pro():
    """Add a custom pro swing manually"""
    print("\n" + "="*60)
    print("ADD CUSTOM PRO SWING")
    print("="*60)
    print("\nNote: This requires you to have already extracted swing metrics.")
    print("For now, this is an advanced feature.\n")
    
    print("To add a custom pro, you need:")
    print("  1. Golfer name")
    print("  2. Club type (Driver, 7-Iron, etc.)")
    print("  3. Swing metrics (hip rotation, shoulder rotation, etc.)")
    print("  4. Optional: Video path and style tags")
    print()
    
    input("Press Enter to return to menu...")


def import_from_video():
    """Import pro swing from video file"""
    print("\n" + "="*60)
    print("IMPORT FROM VIDEO")
    print("="*60)
    print("\n⚠️  This feature requires:")
    print("  1. A video file of the pro swing")
    print("  2. MediaPipe pose analysis (computationally intensive)")
    print("  3. Several minutes to process")
    print()
    print("This is an advanced feature currently under development.")
    print()
    
    # Check if video files exist
    video_dir = Path('./data/pro_videos')
    if video_dir.exists():
        video_files = list(video_dir.glob('*.mp4')) + list(video_dir.glob('*.avi'))
        if video_files:
            print(f"Found {len(video_files)} video(s) in {video_dir}:")
            for vf in video_files[:5]:  # Show first 5
                print(f"  - {vf.name}")
            if len(video_files) > 5:
                print(f"  ... and {len(video_files) - 5} more")
            print()
    
    print("For now, please use Option 1 (Add Sample Pros) to get started.")
    print()
    input("Press Enter to return to menu...")


def clear_database():
    """Clear all pro swings from database"""
    print("\n" + "="*60)
    print("CLEAR DATABASE")
    print("="*60)
    print("\n⚠️  WARNING: This will delete ALL pro swings!")
    print()
    
    confirm = input("Are you sure? Type 'DELETE' to confirm: ").strip()
    if confirm != 'DELETE':
        print("Cancelled.")
        return
    
    try:
        db_path = Path('./data/pro_swings.db')
        if db_path.exists():
            db_path.unlink()
            print("\n✅ Database cleared successfully!")
            print("You can now rebuild it from scratch.\n")
        else:
            print("\n❌ Database file not found.")
    except Exception as e:
        print(f"\n❌ Error clearing database: {e}")


def interactive_menu():
    """Main interactive menu"""
    while True:
        print("\n" + "="*60)
        print("PRO SWING DATABASE BUILDER")
        print("="*60)
        print("\nOptions:")
        print("1. Add sample pro swings (Quick Start - RECOMMENDED)")
        print("2. Check database status")
        print("3. Add custom pro swing (Advanced)")
        print("4. Import from video file (Advanced)")
        print("5. Clear database")
        print("6. Exit")
        print()
        
        choice = input("Select option (1-6): ").strip()
        
        if choice == "1":
            add_sample_pros()
        elif choice == "2":
            check_database_status()
        elif choice == "3":
            add_custom_pro()
        elif choice == "4":
            import_from_video()
        elif choice == "5":
            clear_database()
        elif choice == "6":
            print("\nExiting...")
            break
        else:
            print("\n❌ Invalid option. Please try again.")


def quick_setup():
    """Quick setup - add samples and exit"""
    print_header()
    print("\n🚀 QUICK SETUP MODE")
    print("\nThis will:")
    print("  1. Create the database")
    print("  2. Add 3 sample pro swings")
    print("  3. Verify everything works")
    print()
    
    # Check if database already exists
    if check_database_status():
        print("\n✅ Database already exists with pro swings!")
        print("You're ready to use the system.")
        return
    
    print("\nStarting quick setup...")
    add_sample_pros()
    
    # Verify
    print("\n" + "="*60)
    print("VERIFYING SETUP")
    print("="*60)
    if check_database_status():
        print("\n🎉 SUCCESS! Your database is ready.")
        print("\nNext steps:")
        print("  1. Update config.json with your camera settings")
        print("  2. Run: python promirror/main.py")
        print("  3. Start analyzing swings!")
    else:
        print("\n⚠️  Setup incomplete. Try running the interactive menu.")


def main():
    """Main entry point"""
    # Check if running in quick mode
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_setup()
    else:
        print_header()
        
        # Show current status
        has_pros = check_database_status()
        
        if not has_pros:
            print("\n💡 TIP: Choose option 1 to add sample pros for testing!")
        
        # Start interactive menu
        interactive_menu()
    
    print("\n" + "="*60)
    print("Thank you for using ProMirrorGolf Database Builder!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
