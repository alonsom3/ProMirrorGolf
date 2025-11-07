"""
Swing Database Management
"""
import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SwingDatabase:
    def __init__(self, db_path="./data/swings.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        logger.info(f"Database initialized: {db_path}")
    
    def _init_schema(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS swings (
                swing_id TEXT PRIMARY KEY,
                user_id TEXT,
                timestamp TEXT,
                metrics JSON,
                pro_match_id TEXT,
                video_dtl_path TEXT,
                video_face_path TEXT
            )
        ''')
        
        self.conn.commit()
    
    def save_swing(self, swing_id, user_id, metrics, pro_match_id, video_paths):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO swings (swing_id, user_id, timestamp, metrics, pro_match_id, video_dtl_path, video_face_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            swing_id,
            user_id,
            datetime.now().isoformat(),
            json.dumps(metrics),
            pro_match_id,
            video_paths['dtl'],
            video_paths['face']
        ))
        
        self.conn.commit()
        logger.info(f"Swing saved: {swing_id}")
    
    def get_swing(self, swing_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM swings WHERE swing_id = ?', (swing_id,))
        row = cursor.fetchone()
        
        if row:
            swing = dict(row)
            swing['metrics'] = json.loads(swing['metrics'])
            return swing
        return None