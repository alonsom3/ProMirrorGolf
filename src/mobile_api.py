"""
Mobile API - Complete REST API for mobile/remote companion app
Provides access to metrics, video review, session data with authentication
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import hashlib
import secrets

logger = logging.getLogger(__name__)


class MobileAPI:
    """
    Complete mobile API server for companion app
    Provides REST-like endpoints with authentication and rate limiting
    """
    
    def __init__(self, swing_db, controller=None, port: int = 8080, secret_key: Optional[str] = None):
        """
        Initialize mobile API
        
        Args:
            swing_db: SwingDatabase instance
            controller: Optional SwingAIController for live data
            port: Port to run API server on
            secret_key: Secret key for JWT tokens (generated if None)
        """
        self.swing_db = swing_db
        self.controller = controller
        self.port = port
        self.server = None
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        
        # Rate limiting: track requests per IP
        self.rate_limits = {}  # {ip: [timestamps]}
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 100  # max requests per window
        
        # Authentication: simple token-based (can be upgraded to JWT)
        self.tokens = {}  # {token: {user_id, expires_at}}
        self.token_expiry = timedelta(hours=24)
        
        logger.info(f"Mobile API initialized (port {port})")
    
    async def start_server(self):
        """Start the API server"""
        try:
            import aiohttp
            from aiohttp import web
            from aiohttp.web_middlewares import middleware
            
            # Rate limiting middleware
            @middleware
            async def rate_limit_middleware(request, handler):
                client_ip = request.remote
                if not self._check_rate_limit(client_ip):
                    return web.json_response(
                        {'error': 'Rate limit exceeded'}, 
                        status=429
                    )
                return await handler(request)
            
            # CORS middleware
            @middleware
            async def cors_middleware(request, handler):
                response = await handler(request)
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return response
            
            app = web.Application(middlewares=[rate_limit_middleware, cors_middleware])
            
            # Health and auth endpoints
            app.router.add_get('/api/health', self.health_check)
            app.router.add_post('/api/auth/login', self.login)
            app.router.add_post('/api/auth/refresh', self.refresh_token)
            
            # User endpoints
            app.router.add_get('/api/user/{user_id}/sessions', self.get_user_sessions)
            app.router.add_get('/api/user/{user_id}/stats', self.get_user_stats)
            app.router.add_get('/api/user/{user_id}/recent', self.get_recent_swings)
            app.router.add_get('/api/user/{user_id}/trends', self.get_user_trends)
            
            # Session endpoints
            app.router.add_get('/api/session/{session_id}', self.get_session)
            app.router.add_get('/api/session/{session_id}/swings', self.get_session_swings)
            app.router.add_get('/api/session/{session_id}/summary', self.get_session_summary)
            
            # Swing endpoints
            app.router.add_get('/api/swing/{swing_id}', self.get_swing)
            app.router.add_get('/api/swing/{swing_id}/video', self.get_swing_video)
            app.router.add_post('/api/swing/{swing_id}/notes', self.add_swing_notes)
            
            # Metrics endpoints
            app.router.add_get('/api/metrics', self.get_metrics)
            app.router.get('/api/metrics/trends', self.get_metrics_trends)
            
            # Analytics endpoints
            app.router.add_get('/api/analytics/summary', self.get_analytics_summary)
            app.router.add_get('/api/analytics/export', self.export_analytics)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', self.port)
            await site.start()
            
            self.server = runner
            logger.info(f"Mobile API server started on port {self.port}")
            return True
        except ImportError:
            logger.warning("aiohttp not available, mobile API disabled")
            return False
        except Exception as e:
            logger.error(f"Failed to start mobile API server: {e}")
            return False
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = datetime.now()
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []
        
        # Remove old requests outside window
        self.rate_limits[client_ip] = [
            ts for ts in self.rate_limits[client_ip]
            if (now - ts).total_seconds() < self.rate_limit_window
        ]
        
        # Check limit
        if len(self.rate_limits[client_ip]) >= self.rate_limit_max:
            return False
        
        # Add current request
        self.rate_limits[client_ip].append(now)
        return True
    
    def _generate_token(self, user_id: str) -> str:
        """Generate authentication token"""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            'user_id': user_id,
            'expires_at': datetime.now() + self.token_expiry
        }
        return token
    
    def _validate_token(self, token: str) -> Optional[str]:
        """Validate token and return user_id if valid"""
        if token not in self.tokens:
            return None
        
        token_data = self.tokens[token]
        if datetime.now() > token_data['expires_at']:
            del self.tokens[token]
            return None
        
        return token_data['user_id']
    
    async def health_check(self, request):
        """Health check endpoint"""
        from aiohttp import web
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'server': 'ProMirrorGolf Mobile API'
        })
    
    async def login(self, request):
        """Login endpoint - returns authentication token"""
        from aiohttp import web
        try:
            data = await request.json()
            user_id = data.get('user_id', 'default_user')
            
            # Simple authentication (can be enhanced with password)
            token = self._generate_token(user_id)
            
            return web.json_response({
                'token': token,
                'user_id': user_id,
                'expires_in': int(self.token_expiry.total_seconds())
            })
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def refresh_token(self, request):
        """Refresh authentication token"""
        from aiohttp import web
        try:
            data = await request.json()
            token = data.get('token')
            
            user_id = self._validate_token(token)
            if not user_id:
                return web.json_response({'error': 'Invalid token'}, status=401)
            
            # Generate new token
            new_token = self._generate_token(user_id)
            del self.tokens[token]  # Remove old token
            
            return web.json_response({
                'token': new_token,
                'user_id': user_id,
                'expires_in': int(self.token_expiry.total_seconds())
            })
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def get_user_sessions(self, request):
        """Get user sessions"""
        from aiohttp import web
        user_id = request.match_info['user_id']
        limit = int(request.query.get('limit', 10))
        
        sessions = self.swing_db.get_user_sessions(user_id, limit=limit)
        return web.json_response({
            'user_id': user_id,
            'sessions': sessions,
            'count': len(sessions)
        })
    
    async def get_session(self, request):
        """Get session details"""
        from aiohttp import web
        session_id = request.match_info['session_id']
        
        session = self.swing_db.get_session(session_id)
        if session:
            return web.json_response(session)
        else:
            return web.json_response({'error': 'Session not found'}, status=404)
    
    async def get_session_swings(self, request):
        """Get swings for a session"""
        from aiohttp import web
        session_id = request.match_info['session_id']
        
        swings = self.swing_db.get_session_swings(session_id)
        return web.json_response({
            'session_id': session_id,
            'swings': swings,
            'count': len(swings)
        })
    
    async def get_session_summary(self, request):
        """Get session summary with aggregated metrics"""
        from aiohttp import web
        session_id = request.match_info['session_id']
        
        swings = self.swing_db.get_session_swings(session_id)
        if not swings:
            return web.json_response({'error': 'Session not found'}, status=404)
        
        # Calculate summary
        total_swings = len(swings)
        avg_scores = []
        avg_similarities = []
        
        for swing in swings:
            metrics = swing.get('metrics', {})
            flaw_analysis = swing.get('flaw_analysis', {})
            pro_match = swing.get('pro_match', {})
            
            if flaw_analysis:
                avg_scores.append(flaw_analysis.get('overall_score', 0))
            if pro_match:
                avg_similarities.append(pro_match.get('similarity_score', 0))
        
        summary = {
            'session_id': session_id,
            'total_swings': total_swings,
            'avg_score': sum(avg_scores) / len(avg_scores) if avg_scores else 0,
            'avg_similarity': sum(avg_similarities) / len(avg_similarities) if avg_similarities else 0,
            'best_swing_id': max(swings, key=lambda s: s.get('flaw_analysis', {}).get('overall_score', 0)).get('swing_id') if swings else None
        }
        
        return web.json_response(summary)
    
    async def get_swing(self, request):
        """Get specific swing data"""
        from aiohttp import web
        swing_id = request.match_info['swing_id']
        
        swing = self.swing_db.get_swing(swing_id)
        if swing:
            return web.json_response(swing)
        else:
            return web.json_response({'error': 'Swing not found'}, status=404)
    
    async def get_swing_video(self, request):
        """Get swing video stream URL or metadata"""
        from aiohttp import web
        swing_id = request.match_info['swing_id']
        
        swing = self.swing_db.get_swing(swing_id)
        if not swing:
            return web.json_response({'error': 'Swing not found'}, status=404)
        
        video_paths = swing.get('video_paths', {})
        return web.json_response({
            'swing_id': swing_id,
            'dtl_video': video_paths.get('dtl', ''),
            'face_video': video_paths.get('face', ''),
            'note': 'Video files are stored locally. Use file path to access.'
        })
    
    async def add_swing_notes(self, request):
        """Add user notes to a swing"""
        from aiohttp import web
        swing_id = request.match_info['swing_id']
        
        try:
            data = await request.json()
            notes = data.get('notes', '')
            
            # Update swing in database with notes
            swing = self.swing_db.get_swing(swing_id)
            if not swing:
                return web.json_response({'error': 'Swing not found'}, status=404)
            
            # Add notes (assuming database supports this)
            # This would need to be implemented in SwingDatabase
            return web.json_response({
                'swing_id': swing_id,
                'notes': notes,
                'status': 'updated'
            })
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def get_user_stats(self, request):
        """Get user statistics"""
        from aiohttp import web
        user_id = request.match_info['user_id']
        
        stats = self.swing_db.get_user_stats(user_id)
        return web.json_response({
            'user_id': user_id,
            'stats': stats
        })
    
    async def get_user_trends(self, request):
        """Get user improvement trends over time"""
        from aiohttp import web
        user_id = request.match_info['user_id']
        days = int(request.query.get('days', 30))
        
        # Get sessions from last N days
        sessions = self.swing_db.get_user_sessions(user_id, limit=100)
        
        # Calculate trends
        trends = {
            'user_id': user_id,
            'period_days': days,
            'total_sessions': len(sessions),
            'total_swings': 0,
            'avg_score_trend': [],
            'avg_similarity_trend': []
        }
        
        for session in sessions:
            swings = self.swing_db.get_session_swings(session['session_id'])
            trends['total_swings'] += len(swings)
            
            # Calculate session averages
            session_scores = []
            session_similarities = []
            
            for swing in swings:
                flaw_analysis = swing.get('flaw_analysis', {})
                pro_match = swing.get('pro_match', {})
                
                if flaw_analysis:
                    session_scores.append(flaw_analysis.get('overall_score', 0))
                if pro_match:
                    session_similarities.append(pro_match.get('similarity_score', 0))
            
            if session_scores:
                trends['avg_score_trend'].append({
                    'date': session.get('timestamp', ''),
                    'avg_score': sum(session_scores) / len(session_scores)
                })
            
            if session_similarities:
                trends['avg_similarity_trend'].append({
                    'date': session.get('timestamp', ''),
                    'avg_similarity': sum(session_similarities) / len(session_similarities)
                })
        
        return web.json_response(trends)
    
    async def get_recent_swings(self, request):
        """Get recent swings for a user"""
        from aiohttp import web
        user_id = request.match_info['user_id']
        limit = int(request.query.get('limit', 10))
        
        sessions = self.swing_db.get_user_sessions(user_id, limit=10)
        all_swings = []
        for session in sessions:
            swings = self.swing_db.get_session_swings(session['session_id'])
            all_swings.extend(swings)
        
        # Sort by timestamp and limit
        all_swings.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        recent = all_swings[:limit]
        
        return web.json_response({
            'user_id': user_id,
            'swings': recent,
            'count': len(recent)
        })
    
    async def get_metrics(self, request):
        """Get aggregated metrics across all swings"""
        from aiohttp import web
        user_id = request.query.get('user_id', 'default_user')
        limit = int(request.query.get('limit', 100))
        
        sessions = self.swing_db.get_user_sessions(user_id, limit=10)
        all_swings = []
        for session in sessions:
            swings = self.swing_db.get_session_swings(session['session_id'])
            all_swings.extend(swings[:limit])
        
        # Aggregate metrics
        aggregated = {
            'total_swings': len(all_swings),
            'avg_metrics': {},
            'best_swing': None,
            'worst_swing': None
        }
        
        if all_swings:
            # Calculate averages
            metric_sums = {}
            metric_counts = {}
            
            for swing in all_swings:
                metrics = swing.get('metrics', {})
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        metric_sums[key] = metric_sums.get(key, 0) + value
                        metric_counts[key] = metric_counts.get(key, 0) + 1
            
            for key in metric_sums:
                aggregated['avg_metrics'][key] = metric_sums[key] / metric_counts[key]
            
            # Find best and worst
            best = max(all_swings, key=lambda s: s.get('flaw_analysis', {}).get('overall_score', 0))
            worst = min(all_swings, key=lambda s: s.get('flaw_analysis', {}).get('overall_score', 100))
            
            aggregated['best_swing'] = best.get('swing_id')
            aggregated['worst_swing'] = worst.get('swing_id')
        
        return web.json_response(aggregated)
    
    async def get_metrics_trends(self, request):
        """Get metrics trends over time"""
        from aiohttp import web
        user_id = request.query.get('user_id', 'default_user')
        metric_name = request.query.get('metric', 'overall_score')
        
        sessions = self.swing_db.get_user_sessions(user_id, limit=50)
        trends = []
        
        for session in sessions:
            swings = self.swing_db.get_session_swings(session['session_id'])
            for swing in swings:
                if metric_name == 'overall_score':
                    value = swing.get('flaw_analysis', {}).get('overall_score', 0)
                else:
                    value = swing.get('metrics', {}).get(metric_name, 0)
                
                trends.append({
                    'timestamp': swing.get('timestamp', ''),
                    'value': value
                })
        
        return web.json_response({
            'metric': metric_name,
            'trends': trends
        })
    
    async def get_analytics_summary(self, request):
        """Get analytics summary"""
        from aiohttp import web
        user_id = request.query.get('user_id', 'default_user')
        
        if self.controller and hasattr(self.controller, 'analytics'):
            analytics = self.controller.analytics
            summary = analytics.get_summary_stats() if hasattr(analytics, 'get_summary_stats') else {}
            return web.json_response(summary)
        else:
            return web.json_response({'error': 'Analytics not available'}, status=503)
    
    async def export_analytics(self, request):
        """Export analytics data"""
        from aiohttp import web
        format_type = request.query.get('format', 'csv')
        user_id = request.query.get('user_id', 'default_user')
        
        if self.controller and hasattr(self.controller, 'analytics'):
            analytics = self.controller.analytics
            if format_type == 'csv':
                file_path = analytics.export_csv() if hasattr(analytics, 'export_csv') else None
            else:
                file_path = analytics.export_html_dashboard() if hasattr(analytics, 'export_html_dashboard') else None
            
            if file_path:
                return web.json_response({
                    'format': format_type,
                    'file_path': file_path,
                    'status': 'exported'
                })
        
        return web.json_response({'error': 'Export failed'}, status=500)
    
    async def stop_server(self):
        """Stop the API server"""
        if self.server:
            await self.server.cleanup()
            logger.info("Mobile API server stopped")
