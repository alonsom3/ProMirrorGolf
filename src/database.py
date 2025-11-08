"""
Database schema and management for SwingAI
Stores user swings, sessions, and pro swing database
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SwingDatabase:
    """
    Manages user swing data storage
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database with schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                handicap REAL,
                created_at TEXT,
                last_active TEXT
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                session_name TEXT,
                start_time TEXT,
                end_time TEXT,
                swing_count INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Swings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS swings (
                swing_id TEXT PRIMARY KEY,
                session_id TEXT,
                swing_number INTEGER,
                timestamp TEXT,
                
                -- Video paths
                video_dtl_path TEXT,
                video_face_path TEXT,
                
                -- Swing metrics (JSON)
                metrics JSON,
                
                -- Launch monitor data (JSON)
                shot_data JSON,
                
                -- AI analysis
                flaw_analysis JSON,
                overall_score REAL,
                
                -- Pro comparison
                pro_match_id TEXT,
                report_path TEXT,
                
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (pro_match_id) REFERENCES pro_swings(pro_id)
            )
        ''')
        
        # Indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_swings_session 
            ON swings(session_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_swings_timestamp 
            ON swings(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_user 
            ON sessions(user_id)
        ''')
        
        self.conn.commit()
        logger.info(f"Database initialized: {self.db_path}")
    
    def create_user(self, user_id: str, name: str, handicap: float = 0.0) -> str:
        """Create a new user"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, name, handicap, created_at, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, name, handicap, datetime.now().isoformat(), datetime.now().isoformat()))
        
        self.conn.commit()
        logger.info(f"User created: {user_id}")
        return user_id
    
    def create_session(self, user_id: str, session_name: Optional[str] = None) -> str:
        """Create a new practice session"""
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not session_name:
            session_name = f"Practice {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (session_id, user_id, session_name, start_time, swing_count)
            VALUES (?, ?, ?, ?, 0)
        ''', (session_id, user_id, session_name, datetime.now().isoformat()))
        
        self.conn.commit()
        logger.info(f"Session created: {session_id}")
        return session_id
    
    def save_swing(self, session_id: str, swing_id: str, swing_metrics: Dict,
                   shot_data: Dict, video_paths: Dict, report_path: str,
                   pro_match_id: str, flaw_analysis: Optional[Dict] = None):
        """Save a swing to the database"""
        cursor = self.conn.cursor()
        
        # Get current swing count for this session
        cursor.execute('SELECT swing_count FROM sessions WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        swing_number = result[0] + 1 if result else 1
        
        # Insert swing
        cursor.execute('''
            INSERT INTO swings (
                swing_id, session_id, swing_number, timestamp,
                video_dtl_path, video_face_path,
                metrics, shot_data, flaw_analysis, overall_score,
                pro_match_id, report_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            swing_id,
            session_id,
            swing_number,
            datetime.now().isoformat(),
            video_paths['dtl'],
            video_paths['face'],
            json.dumps(swing_metrics),
            json.dumps(shot_data),
            json.dumps(flaw_analysis) if flaw_analysis else None,
            flaw_analysis.get('overall_score', 0) if flaw_analysis else 0,
            pro_match_id,
            report_path
        ))
        
        # Update session swing count
        cursor.execute('''
            UPDATE sessions 
            SET swing_count = swing_count + 1, end_time = ?
            WHERE session_id = ?
        ''', (datetime.now().isoformat(), session_id))
        
        self.conn.commit()
        logger.info(f"Swing saved: {swing_id}")
    
    def get_swing(self, swing_id: str) -> Optional[Dict]:
        """Retrieve a specific swing"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM swings WHERE swing_id = ?', (swing_id,))
        
        row = cursor.fetchone()
        if row:
            swing = dict(row)
            # Parse JSON fields
            swing['metrics'] = json.loads(swing['metrics']) if swing['metrics'] else {}
            swing['shot_data'] = json.loads(swing['shot_data']) if swing['shot_data'] else {}
            swing['flaw_analysis'] = json.loads(swing['flaw_analysis']) if swing['flaw_analysis'] else {}
            return swing
        return None
    
    def get_session_swings(self, session_id: str) -> List[Dict]:
        """Get all swings from a session"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM swings 
            WHERE session_id = ? 
            ORDER BY swing_number
        ''', (session_id,))
        
        swings = []
        for row in cursor.fetchall():
            swing = dict(row)
            swing['metrics'] = json.loads(swing['metrics']) if swing['metrics'] else {}
            swing['shot_data'] = json.loads(swing['shot_data']) if swing['shot_data'] else {}
            swings.append(swing)
        
        return swings
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent sessions for a user"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM sessions 
            WHERE user_id = ? 
            ORDER BY start_time DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def finalize_session(self, session_id: str, swing_count: int):
        """Finalize a session"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET end_time = ?, swing_count = ?
            WHERE session_id = ?
        ''', (datetime.now().isoformat(), swing_count, session_id))
        
        self.conn.commit()
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get overall statistics for a user"""
        cursor = self.conn.cursor()
        
        # Total sessions
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE user_id = ?', (user_id,))
        total_sessions = cursor.fetchone()[0]
        
        # Total swings
        cursor.execute('''
            SELECT COUNT(*) FROM swings 
            WHERE session_id IN (SELECT session_id FROM sessions WHERE user_id = ?)
        ''', (user_id,))
        total_swings = cursor.fetchone()[0]
        
        # Average score
        cursor.execute('''
            SELECT AVG(overall_score) FROM swings 
            WHERE session_id IN (SELECT session_id FROM sessions WHERE user_id = ?)
        ''', (user_id,))
        avg_score = cursor.fetchone()[0] or 0
        
        # Recent improvement (last 10 vs previous 10)
        cursor.execute('''
            SELECT overall_score FROM swings 
            WHERE session_id IN (SELECT session_id FROM sessions WHERE user_id = ?)
            ORDER BY timestamp DESC
            LIMIT 20
        ''', (user_id,))
        
        recent_scores = [row[0] for row in cursor.fetchall()]
        if len(recent_scores) >= 20:
            recent_10 = sum(recent_scores[:10]) / 10
            previous_10 = sum(recent_scores[10:20]) / 10
            improvement = recent_10 - previous_10
        else:
            improvement = 0
        
        return {
            'total_sessions': total_sessions,
            'total_swings': total_swings,
            'average_score': round(avg_score, 1),
            'recent_improvement': round(improvement, 1)
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class ProSwingDatabase:
    """
    Manages the professional swing database
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize pro swing database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pro_swings (
                pro_id TEXT PRIMARY KEY,
                golfer_name TEXT,
                
                -- Video paths
                video_dtl_path TEXT,
                video_face_path TEXT,
                youtube_url TEXT,
                
                -- Swing metrics (JSON)
                metrics JSON,
                
                -- Metadata
                club_type TEXT,
                swing_speed REAL,
                style_tags TEXT,  -- Comma-separated
                
                -- Pre-processed data
                pose_data JSON,
                
                capture_date TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pro_club 
            ON pro_swings(club_type)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pro_tags 
            ON pro_swings(style_tags)
        ''')
        
        self.conn.commit()
        logger.info(f"Pro database initialized: {self.db_path}")
    
    def add_pro_swing(self, pro_id: str, golfer_name: str, video_paths: Dict,
                     metrics: Dict, club_type: str, style_tags: List[str],
                     youtube_url: Optional[str] = None, pose_data: Optional[Dict] = None):
        """Add a professional swing to the database"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO pro_swings (
                pro_id, golfer_name, video_dtl_path, video_face_path,
                youtube_url, metrics, club_type, style_tags, pose_data, capture_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pro_id,
            golfer_name,
            video_paths.get('dtl'),
            video_paths.get('face'),
            youtube_url,
            json.dumps(metrics),
            club_type,
            ','.join(style_tags),
            json.dumps(pose_data) if pose_data else None,
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        logger.info(f"Pro swing added: {golfer_name} - {pro_id}")
    
    def get_pro_swing(self, pro_id: str) -> Optional[Dict]:
        """Get a specific pro swing"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM pro_swings WHERE pro_id = ?', (pro_id,))
        
        row = cursor.fetchone()
        if row:
            swing = dict(row)
            swing['metrics'] = json.loads(swing['metrics']) if swing['metrics'] else {}
            swing['pose_data'] = json.loads(swing['pose_data']) if swing['pose_data'] else {}
            swing['style_tags'] = swing['style_tags'].split(',') if swing['style_tags'] else []
            return swing
        return None
    
    def get_all_pro_swings(self, club_type: Optional[str] = None) -> List[Dict]:
        """Get all pro swings, optionally filtered by club"""
        cursor = self.conn.cursor()
        
        if club_type:
            cursor.execute('SELECT * FROM pro_swings WHERE club_type = ?', (club_type,))
        else:
            cursor.execute('SELECT * FROM pro_swings')
        
        swings = []
        for row in cursor.fetchall():
            swing = dict(row)
            swing['metrics'] = json.loads(swing['metrics']) if swing['metrics'] else {}
            swing['style_tags'] = swing['style_tags'].split(',') if swing['style_tags'] else []
            swings.append(swing)
        
        return swings
    
    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()