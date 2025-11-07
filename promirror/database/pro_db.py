"""
Professional Swing Database Manager
Stores and retrieves professional golf swing data for comparison
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProSwingDatabase:
    """
    Manages the professional swing reference database.
    Stores metrics, video paths, and metadata for pro golfers.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database with schema"""
        # Create directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        cursor = self.conn.cursor()
        
        # Create pro_swings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pro_swings (
                pro_id TEXT PRIMARY KEY,
                golfer_name TEXT NOT NULL,
                club_type TEXT NOT NULL,
                video_path TEXT,
                metrics TEXT NOT NULL,
                style_tags TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        ''')
        
        # Create index for faster club_type queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_club_type 
            ON pro_swings(club_type)
        ''')
        
        self.conn.commit()
        logger.info(f"Pro database initialized: {self.db_path}")
    
    def add_pro_swing(self, pro_id: str, golfer_name: str, club_type: str,
                     metrics: Dict, video_path: str = None,
                     style_tags: List[str] = None, notes: str = None):
        """
        Add or update a professional swing in the database.
        
        Args:
            pro_id: Unique identifier (e.g., "rory_driver")
            golfer_name: Full name (e.g., "Rory McIlroy")
            club_type: Club used (e.g., "Driver", "7-Iron")
            metrics: Dictionary of swing metrics
            video_path: Optional path to swing video
            style_tags: Optional list of style descriptors
            notes: Optional notes about this swing
        """
        cursor = self.conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO pro_swings
            (pro_id, golfer_name, club_type, video_path, metrics, 
             style_tags, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pro_id,
            golfer_name,
            club_type,
            video_path,
            json.dumps(metrics),
            ','.join(style_tags) if style_tags else '',
            notes,
            now,
            now
        ))
        
        self.conn.commit()
        logger.info(f"✓ Added pro swing: {golfer_name} ({club_type})")
    
    def get_all_pros(self, club_type: str = None) -> List[Dict]:
        """
        Get all professional swings, optionally filtered by club type.
        
        Args:
            club_type: Optional filter (e.g., "Driver", "7-Iron")
            
        Returns:
            List of pro swing dictionaries
        """
        cursor = self.conn.cursor()
        
        if club_type:
            cursor.execute(
                'SELECT * FROM pro_swings WHERE club_type = ?',
                (club_type,)
            )
        else:
            cursor.execute('SELECT * FROM pro_swings')
        
        pros = []
        for row in cursor.fetchall():
            pro = dict(row)
            # Parse JSON fields
            pro['metrics'] = json.loads(pro['metrics'])
            pro['style_tags'] = pro['style_tags'].split(',') if pro['style_tags'] else []
            pros.append(pro)
        
        logger.debug(f"Retrieved {len(pros)} pro swings" + 
                    (f" for {club_type}" if club_type else ""))
        
        return pros
    
    def get_pro_by_id(self, pro_id: str) -> Optional[Dict]:
        """
        Get a specific pro swing by ID.
        
        Args:
            pro_id: Pro swing identifier
            
        Returns:
            Pro swing dictionary, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM pro_swings WHERE pro_id = ?', (pro_id,))
        
        row = cursor.fetchone()
        if row:
            pro = dict(row)
            pro['metrics'] = json.loads(pro['metrics'])
            pro['style_tags'] = pro['style_tags'].split(',') if pro['style_tags'] else []
            return pro
        
        logger.warning(f"Pro swing not found: {pro_id}")
        return None
    
    def get_pro_by_name(self, golfer_name: str, club_type: str = None) -> Optional[Dict]:
        """
        Get a pro swing by golfer name.
        
        Args:
            golfer_name: Name to search for (case-insensitive)
            club_type: Optional club type filter
            
        Returns:
            Pro swing dictionary, or None if not found
        """
        cursor = self.conn.cursor()
        
        if club_type:
            cursor.execute(
                'SELECT * FROM pro_swings WHERE LOWER(golfer_name) = LOWER(?) AND club_type = ?',
                (golfer_name, club_type)
            )
        else:
            cursor.execute(
                'SELECT * FROM pro_swings WHERE LOWER(golfer_name) = LOWER(?)',
                (golfer_name,)
            )
        
        row = cursor.fetchone()
        if row:
            pro = dict(row)
            pro['metrics'] = json.loads(pro['metrics'])
            pro['style_tags'] = pro['style_tags'].split(',') if pro['style_tags'] else []
            return pro
        
        return None
    
    def update_pro_metrics(self, pro_id: str, metrics: Dict):
        """Update metrics for an existing pro swing"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE pro_swings 
            SET metrics = ?, updated_at = ?
            WHERE pro_id = ?
        ''', (json.dumps(metrics), datetime.now().isoformat(), pro_id))
        
        self.conn.commit()
        logger.info(f"Updated metrics for {pro_id}")
    
    def delete_pro(self, pro_id: str):
        """Delete a pro swing from the database"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM pro_swings WHERE pro_id = ?', (pro_id,))
        self.conn.commit()
        logger.info(f"Deleted pro swing: {pro_id}")
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database"""
        cursor = self.conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM pro_swings')
        total_count = cursor.fetchone()[0]
        
        # Count by club type
        cursor.execute('''
            SELECT club_type, COUNT(*) as count 
            FROM pro_swings 
            GROUP BY club_type
        ''')
        by_club = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Unique golfers
        cursor.execute('SELECT COUNT(DISTINCT golfer_name) FROM pro_swings')
        unique_golfers = cursor.fetchone()[0]
        
        return {
            'total_swings': total_count,
            'unique_golfers': unique_golfers,
            'by_club_type': by_club
        }
    
    def list_all_golfers(self) -> List[str]:
        """Get list of all golfer names in database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT golfer_name FROM pro_swings ORDER BY golfer_name')
        return [row[0] for row in cursor.fetchall()]
    
    def search_pros(self, search_term: str) -> List[Dict]:
        """
        Search for pros by name or style tags.
        
        Args:
            search_term: Term to search for (case-insensitive)
            
        Returns:
            List of matching pro swings
        """
        cursor = self.conn.cursor()
        
        search_pattern = f'%{search_term}%'
        cursor.execute('''
            SELECT * FROM pro_swings 
            WHERE LOWER(golfer_name) LIKE LOWER(?)
               OR LOWER(style_tags) LIKE LOWER(?)
        ''', (search_pattern, search_pattern))
        
        pros = []
        for row in cursor.fetchall():
            pro = dict(row)
            pro['metrics'] = json.loads(pro['metrics'])
            pro['style_tags'] = pro['style_tags'].split(',') if pro['style_tags'] else []
            pros.append(pro)
        
        return pros
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Pro database connection closed")


def create_sample_pro_data():
    """
    Create sample pro swing data for testing.
    Returns a list of sample pro dictionaries.
    """
    return [
        {
            'pro_id': 'rory_driver',
            'golfer_name': 'Rory McIlroy',
            'club_type': 'Driver',
            'metrics': {
                'hip_rotation': 45,
                'shoulder_rotation': 105,
                'x_factor': 52,
                'spine_angle': 35,
                'weight_transfer': 0.12,
                'tempo_ratio': 3.1,
                'backswing_time': 0.90,
                'club_speed': 120
            },
            'style_tags': ['power', 'athletic', 'modern', 'full_turn'],
            'notes': 'One of the longest hitters on tour with excellent athleticism'
        },
        {
            'pro_id': 'adam_driver',
            'golfer_name': 'Adam Scott',
            'club_type': 'Driver',
            'metrics': {
                'hip_rotation': 42,
                'shoulder_rotation': 95,
                'x_factor': 48,
                'spine_angle': 32,
                'weight_transfer': 0.09,
                'tempo_ratio': 3.2,
                'backswing_time': 0.95,
                'club_speed': 112
            },
            'style_tags': ['smooth', 'classic', 'balanced_tempo', 'full_turn'],
            'notes': 'Classic, smooth swing with excellent tempo'
        },
        {
            'pro_id': 'tiger_driver',
            'golfer_name': 'Tiger Woods',
            'club_type': 'Driver',
            'metrics': {
                'hip_rotation': 40,
                'shoulder_rotation': 100,
                'x_factor': 55,
                'spine_angle': 34,
                'weight_transfer': 0.11,
                'tempo_ratio': 2.9,
                'backswing_time': 0.85,
                'club_speed': 118
            },
            'style_tags': ['stacked', 'modern', 'power', 'high_separation'],
            'notes': 'Legendary modern swing with exceptional control and power'
        }
    ]


# Test function
def test_pro_database():
    """Test the pro database"""
    print("Testing Pro Swing Database...")
    print()
    
    # Initialize database
    db = ProSwingDatabase('./data/pro_swings.db')
    
    # Add sample pros
    print("Adding sample pro swings...")
    for pro_data in create_sample_pro_data():
        db.add_pro_swing(**pro_data)
    
    # Get statistics
    stats = db.get_database_stats()
    print(f"\nDatabase Stats:")
    print(f"  Total swings: {stats['total_swings']}")
    print(f"  Unique golfers: {stats['unique_golfers']}")
    print(f"  By club type: {stats['by_club_type']}")
    
    # List all golfers
    print(f"\nGolfers in database:")
    for name in db.list_all_golfers():
        print(f"  - {name}")
    
    # Get all drivers
    print(f"\nDriver swings:")
    drivers = db.get_all_pros(club_type='Driver')
    for pro in drivers:
        print(f"  - {pro['golfer_name']}: {pro['metrics']['club_speed']} mph")
    
    # Search test
    print(f"\nSearching for 'modern':")
    results = db.search_pros('modern')
    for pro in results:
        print(f"  - {pro['golfer_name']}")
    
    db.close()
    print("\n✓ Test complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_pro_database()
