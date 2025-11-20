"""REST API backend for web dashboard."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for web frontend

# Store session_manager on app for route handlers
app.session_manager = None


def create_api(session_manager, host: str = "127.0.0.1", port: int = 5000):
    """Create and configure Flask API."""
    # Store session_manager on app object so routes can access it
    app.session_manager = session_manager
    
    @app.route('/api/sessions', methods=['GET'])
    def get_sessions():
        """Get all sessions."""
        try:
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel
            
            if not app.session_manager or not app.session_manager.engine:
                return jsonify({'error': 'Database not initialized'}), 500
            
            # Get query parameters
            club = request.args.get('club')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            with Session(app.session_manager.engine) as session:
                query = session.query(SessionModel)
                
                if club:
                    query = query.filter(SessionModel.club == club)
                
                if start_date:
                    start = datetime.fromisoformat(start_date)
                    query = query.filter(SessionModel.started_at >= start)
                
                if end_date:
                    end = datetime.fromisoformat(end_date)
                    # Include full end date
                    end = end.replace(hour=23, minute=59, second=59)
                    query = query.filter(SessionModel.started_at <= end)
                
                sessions = query.order_by(SessionModel.started_at.desc()).all()
                
                result = []
                for sess in sessions:
                    result.append({
                        'id': sess.id,
                        'name': sess.name,
                        'club': sess.club,
                        'started_at': sess.started_at.isoformat() if sess.started_at else None,
                        'ended_at': sess.ended_at.isoformat() if sess.ended_at else None,
                        'notes': sess.notes,
                        'shot_count': len(sess.shots) if sess.shots else 0,
                    })
                
                return jsonify({'sessions': result})
        except Exception as e:
            logger.error("Error getting sessions: %s", e, exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sessions/<int:session_id>', methods=['GET'])
    def get_session(session_id: int):
        """Get a specific session."""
        try:
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel
            
            if not app.session_manager or not app.session_manager.engine:
                return jsonify({'error': 'Database not initialized'}), 500
            
            with Session(app.session_manager.engine) as session:
                sess = session.get(SessionModel, session_id)
                if not sess:
                    return jsonify({'error': 'Session not found'}), 404
                
                shots = []
                for shot in sess.shots:
                    shots.append({
                        'id': shot.id,
                        'recorded_at': shot.recorded_at.isoformat() if shot.recorded_at else None,
                        'club_speed': shot.club_speed,
                        'ball_speed': shot.ball_speed,
                        'carry_distance': shot.carry_distance,
                        'total_distance': shot.total_distance,
                        'spin_rate': shot.spin_rate,
                        'launch_angle': shot.launch_angle,
                        'notes': shot.notes,
                    })
                
                return jsonify({
                    'id': sess.id,
                    'name': sess.name,
                    'club': sess.club,
                    'started_at': sess.started_at.isoformat() if sess.started_at else None,
                    'ended_at': sess.ended_at.isoformat() if sess.ended_at else None,
                    'notes': sess.notes,
                    'shots': shots,
                })
        except Exception as e:
            logger.error("Error getting session: %s", e, exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/shots', methods=['GET'])
    def get_shots():
        """Get shots with optional filters."""
        try:
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel, ShotModel
            
            # Get query parameters
            session_id = request.args.get('session_id', type=int)
            club = request.args.get('club')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            limit = request.args.get('limit', type=int, default=1000)
            
            if not app.session_manager or not app.session_manager.engine:
                return jsonify({'error': 'Database not initialized'}), 500
            
            with Session(app.session_manager.engine) as session:
                query = session.query(ShotModel)
                
                if session_id:
                    query = query.filter(ShotModel.session_id == session_id)
                
                if club or start_date or end_date:
                    query = query.join(SessionModel)
                    
                    if club:
                        query = query.filter(SessionModel.club == club)
                    
                    if start_date:
                        start = datetime.fromisoformat(start_date)
                        query = query.filter(SessionModel.started_at >= start)
                    
                    if end_date:
                        end = datetime.fromisoformat(end_date)
                        # Include full end date
                        end = end.replace(hour=23, minute=59, second=59)
                        query = query.filter(SessionModel.started_at <= end)
                
                shots = query.order_by(ShotModel.recorded_at.desc()).limit(limit).all()
                
                # Get session map for club info
                session_map = {}
                for shot in shots:
                    if shot.session_id not in session_map:
                        sess = session.get(SessionModel, shot.session_id)
                        session_map[shot.session_id] = sess.club if sess and sess.club else None
                
                result = []
                for shot in shots:
                    result.append({
                        'id': shot.id,
                        'session_id': shot.session_id,
                        'club': session_map.get(shot.session_id),
                        'recorded_at': shot.recorded_at.isoformat() if shot.recorded_at else None,
                        'club_speed': shot.club_speed,
                        'ball_speed': shot.ball_speed,
                        'carry_distance': shot.carry_distance,
                        'total_distance': shot.total_distance,
                        'spin_rate': shot.spin_rate,
                        'launch_angle': shot.launch_angle,
                        'launch_direction': shot.launch_direction,
                        'side_spin': shot.side_spin,
                        'back_spin': shot.back_spin,
                        'apex_height': shot.apex_height,
                        'descent_angle': shot.descent_angle,
                        'smash_factor': shot.smash_factor,
                        'dynamic_loft': shot.dynamic_loft,
                        'attack_angle': shot.attack_angle,
                        'club_path': shot.club_path,
                        'face_angle': shot.face_angle,
                        'notes': shot.notes,
                    })
                
                return jsonify({'shots': result, 'count': len(result)})
        except Exception as e:
            logger.error("Error getting shots: %s", e, exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get summary statistics."""
        try:
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel, ShotModel
            
            # Get query parameters
            club = request.args.get('club')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if not app.session_manager or not app.session_manager.engine:
                return jsonify({'error': 'Database not initialized'}), 500
            
            with Session(app.session_manager.engine) as session:
                query = session.query(ShotModel)
                
                if club or start_date or end_date:
                    query = query.join(SessionModel)
                    
                    if club:
                        query = query.filter(SessionModel.club == club)
                    
                    if start_date:
                        start = datetime.fromisoformat(start_date)
                        query = query.filter(SessionModel.started_at >= start)
                    
                    if end_date:
                        end = datetime.fromisoformat(end_date)
                        # Include full end date
                        end = end.replace(hour=23, minute=59, second=59)
                        query = query.filter(SessionModel.started_at <= end)
                
                shots = query.all()
                
                club_speeds = [s.club_speed for s in shots if s.club_speed]
                ball_speeds = [s.ball_speed for s in shots if s.ball_speed]
                carries = [s.carry_distance for s in shots if s.carry_distance]
                spins = [s.spin_rate for s in shots if s.spin_rate]
                
                # Calculate consistency (standard deviation)
                consistency = None
                if len(carries) > 1:
                    import statistics
                    try:
                        consistency = statistics.stdev(carries)
                    except:
                        pass
                
                # Calculate additional statistics
                min_carry = min(carries) if carries else None
                total_distance = [s.total_distance for s in shots if s.total_distance]
                avg_total_distance = sum(total_distance) / len(total_distance) if total_distance else None
                max_total_distance = max(total_distance) if total_distance else None
                
                # Calculate ranges
                club_speed_range = (min(club_speeds), max(club_speeds)) if club_speeds else None
                ball_speed_range = (min(ball_speeds), max(ball_speeds)) if ball_speeds else None
                carry_range = (min_carry, max(carries)) if carries else None
                
                # Calculate standard deviations
                import statistics
                club_speed_std = statistics.stdev(club_speeds) if len(club_speeds) > 1 else None
                ball_speed_std = statistics.stdev(ball_speeds) if len(ball_speeds) > 1 else None
                carry_std = consistency
                
                stats = {
                    'total_shots': len(shots),
                    'total_sessions': len(set(s.session_id for s in shots)),
                    'avg_club_speed': sum(club_speeds) / len(club_speeds) if club_speeds else None,
                    'avg_ball_speed': sum(ball_speeds) / len(ball_speeds) if ball_speeds else None,
                    'avg_carry': sum(carries) / len(carries) if carries else None,
                    'min_carry': min_carry,
                    'max_carry': max(carries) if carries else None,
                    'avg_total_distance': avg_total_distance,
                    'max_total_distance': max_total_distance,
                    'avg_spin_rate': sum(spins) / len(spins) if spins else None,
                    'consistency': consistency,
                    'club_speed_range': club_speed_range,
                    'ball_speed_range': ball_speed_range,
                    'carry_range': carry_range,
                    'club_speed_std': club_speed_std,
                    'ball_speed_std': ball_speed_std,
                    'carry_std': carry_std,
                }
                
                return jsonify(stats)
        except Exception as e:
            logger.error("Error getting stats: %s", e, exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/clubs', methods=['GET'])
    def get_clubs():
        """Get list of clubs."""
        try:
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel
            
            if not app.session_manager or not app.session_manager.engine:
                return jsonify({'error': 'Database not initialized'}), 500
            
            with Session(app.session_manager.engine) as session:
                clubs = session.query(SessionModel.club).distinct().filter(
                    SessionModel.club.isnot(None)
                ).all()
                
                result = [club[0] for club in clubs if club[0]]
                return jsonify({'clubs': result})
        except Exception as e:
            logger.error("Error getting clubs: %s", e, exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/test', methods=['GET'])
    def test_connection():
        """Test API connection and database."""
        try:
            if not app.session_manager:
                return jsonify({'error': 'Session manager not initialized', 'status': 'error'}), 500
            
            if not app.session_manager.engine:
                return jsonify({'error': 'Database engine not initialized', 'status': 'error'}), 500
            
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel
            
            with Session(app.session_manager.engine) as session:
                count = session.query(SessionModel).count()
            
            return jsonify({
                'status': 'ok',
                'message': 'API and database connected',
                'session_count': count
            })
        except Exception as e:
            logger.error("Error testing connection: %s", e, exc_info=True)
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/share/<share_id>', methods=['GET'])
    def get_shared_view(share_id: str):
        """Get a shared view by ID."""
        try:
            from sqlalchemy.orm import Session
            from core.session_manager import SessionModel, ShotModel
            
            if not app.session_manager or not app.session_manager.engine:
                return jsonify({'error': 'Database not initialized'}), 500
            
            with Session(app.session_manager.engine) as session:
                if share_id.startswith('session_'):
                    session_id = int(share_id.split('_')[1])
                    sess = session.get(SessionModel, session_id)
                    if sess:
                        shots = list(sess.shots) if sess.shots else []
                        return jsonify({
                            'type': 'session',
                            'session': {
                                'id': sess.id,
                                'name': sess.name,
                                'club': sess.club,
                                'started_at': sess.started_at.isoformat(),
                                'shot_count': len(shots),
                            },
                            'shots': [{
                                'id': s.id,
                                'recorded_at': s.recorded_at.isoformat(),
                                'club_speed': s.club_speed,
                                'ball_speed': s.ball_speed,
                                'carry_distance': s.carry_distance,
                            } for s in shots[:50]],
                        })
                
                elif share_id.startswith('shot_'):
                    shot_id = int(share_id.split('_')[1])
                    shot = session.get(ShotModel, shot_id)
                    if shot:
                        return jsonify({
                            'type': 'shot',
                            'shot': {
                                'id': shot.id,
                                'recorded_at': shot.recorded_at.isoformat(),
                                'club_speed': shot.club_speed,
                                'ball_speed': shot.ball_speed,
                                'carry_distance': shot.carry_distance,
                            },
                        })
            
            return jsonify({'error': 'Not found'}), 404
        except Exception as e:
            logger.error("Error getting shared view: %s", e, exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/generate_share_link', methods=['POST'])
    def generate_share_link():
        """Generate a shareable link for a session or shot."""
        try:
            data = request.get_json()
            share_type = data.get('type')
            item_id = data.get('id')
            
            if not share_type or not item_id:
                return jsonify({'error': 'Missing type or id'}), 400
            
            share_id = f"{share_type}_{item_id}"
            share_url = f"http://127.0.0.1:5000/share/{share_id}"
            
            return jsonify({
                'share_id': share_id,
                'share_url': share_url,
            })
        except Exception as e:
            logger.error("Error generating share link: %s", e, exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/')
    def index():
        """Serve the web dashboard."""
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        """Serve static files."""
        return send_from_directory(app.static_folder, path)
    
    return app


def run_api(session_manager, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Run the API server."""
    app = create_api(session_manager, host, port)
    logger.info("Starting web API server on http://%s:%d", host, port)
    app.run(host=host, port=port, debug=debug)

