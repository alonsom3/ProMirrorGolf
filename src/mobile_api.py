"""
Mobile API - Basic REST API for mobile/remote companion app
Provides access to metrics, video review, and session data
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MobileAPI:
    """
    Basic mobile API server for companion app
    Provides REST-like endpoints for accessing swing data
    """
    
    def __init__(self, swing_db, controller=None, port: int = 8080):
        """
        Initialize mobile API
        
        Args:
            swing_db: SwingDatabase instance
            controller: Optional SwingAIController for live data
            port: Port to run API server on
        """
        self.swing_db = swing_db
        self.controller = controller
        self.port = port
        self.server = None
        logger.info(f"Mobile API initialized (port {port})")
    
    async def start_server(self):
        """Start the API server"""
        try:
            import aiohttp
            from aiohttp import web
            
            app = web.Application()
            app.router.add_get('/api/health', self.health_check)
            app.router.add_get('/api/user/{user_id}/sessions', self.get_user_sessions)
            app.router.add_get('/api/session/{session_id}/swings', self.get_session_swings)
            app.router.add_get('/api/swing/{swing_id}', self.get_swing)
            app.router.add_get('/api/user/{user_id}/stats', self.get_user_stats)
            app.router.add_get('/api/user/{user_id}/recent', self.get_recent_swings)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', self.port)
            await site.start()
            
            logger.info(f"Mobile API server started on port {self.port}")
            return True
        except ImportError:
            logger.warning("aiohttp not available, mobile API disabled")
            return False
        except Exception as e:
            logger.error(f"Failed to start mobile API server: {e}")
            return False
    
    async def health_check(self, request):
        """Health check endpoint"""
        from aiohttp import web
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
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
    
    async def get_swing(self, request):
        """Get specific swing data"""
        from aiohttp import web
        swing_id = request.match_info['swing_id']
        
        swing = self.swing_db.get_swing(swing_id)
        if swing:
            return web.json_response(swing)
        else:
            return web.json_response({'error': 'Swing not found'}, status=404)
    
    async def get_user_stats(self, request):
        """Get user statistics"""
        from aiohttp import web
        user_id = request.match_info['user_id']
        
        stats = self.swing_db.get_user_stats(user_id)
        return web.json_response({
            'user_id': user_id,
            'stats': stats
        })
    
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
    
    async def stop_server(self):
        """Stop the API server"""
        if self.server:
            await self.server.shutdown()
            logger.info("Mobile API server stopped")

