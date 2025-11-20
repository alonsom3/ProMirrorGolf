"""Database query optimization utilities."""

from __future__ import annotations

import logging
import functools
from typing import Optional, TypeVar, Generic, Callable, Any
from sqlalchemy.orm import Session, Query, joinedload
from sqlalchemy import Index

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Simple in-memory cache for query results
_query_cache: dict[str, tuple[Any, float]] = {}
_cache_ttl = 300  # 5 minutes


class QueryOptimizer:
    """Utilities for optimizing database queries."""
    
    @staticmethod
    def paginate_query(
        query: Query[T],
        page: int = 1,
        per_page: int = 100,
    ) -> tuple[Query[T], int]:
        """
        Paginate a query.
        
        Args:
            query: SQLAlchemy query
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Tuple of (paginated query, total count)
        """
        total = query.count()
        offset = (page - 1) * per_page
        
        paginated_query = query.offset(offset).limit(per_page)
        return paginated_query, total
    
    @staticmethod
    def optimize_shot_query(
        query: Query,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        eager_load: bool = True,
    ) -> Query:
        """
        Optimize a shot query with eager loading and pagination.
        
        Args:
            query: Base query for shots
            limit: Maximum number of results
            offset: Number of results to skip
            eager_load: Whether to eager load relationships
            
        Returns:
            Optimized query
        """
        from core.session_manager import ShotModel, SessionModel
        
        if eager_load:
            # Eager load session relationship to avoid N+1 queries
            query = query.options(
                joinedload(ShotModel.session)
            )
        
        if offset is not None:
            query = query.offset(offset)
        
        if limit is not None:
            query = query.limit(limit)
        
        return query
    
    @staticmethod
    def create_indexes(session: Session) -> None:
        """
        Create database indexes for common query patterns.
        
        Args:
            session: Database session
        """
        from core.session_manager import ShotModel, SessionModel
        from sqlalchemy import text
        
        try:
            # Index on shot.session_id (most common join)
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shots_session_id 
                ON shots(session_id)
            """))
            
            # Index on shot.recorded_at (common for date filtering)
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shots_recorded_at 
                ON shots(recorded_at)
            """))
            
            # Index on session.started_at (common for date filtering)
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sessions_started_at 
                ON sessions(started_at)
            """))
            
            # Index on session.club (common for filtering)
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sessions_club 
                ON sessions(club)
            """))
            
            # Composite index for common query pattern
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_shots_session_recorded 
                ON shots(session_id, recorded_at)
            """))
            
            session.commit()
            logger.info("Database indexes created successfully")
        except Exception as e:
            session.rollback()
            logger.error("Error creating indexes: %s", e, exc_info=True)
    
    @staticmethod
    def get_shot_count(
        session: Session,
        session_id: Optional[int] = None,
    ) -> int:
        """
        Get count of shots efficiently.
        
        Args:
            session: Database session
            session_id: Optional session ID to filter by
            
        Returns:
            Count of shots
        """
        from core.session_manager import ShotModel
        
        query = session.query(ShotModel)
        if session_id:
            query = query.filter(ShotModel.session_id == session_id)
        
        return query.count()
    
    @staticmethod
    def cached_query(cache_key: str, ttl: float = _cache_ttl):
        """Decorator to cache query results.
        
        Args:
            cache_key: Cache key prefix
            ttl: Time to live in seconds
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function args
                key = f"{cache_key}:{str(args)}:{str(kwargs)}"
                
                # Check cache
                if key in _query_cache:
                    result, timestamp = _query_cache[key]
                    if time.time() - timestamp < ttl:
                        logger.debug("Cache hit for %s", key)
                        return result
                    else:
                        # Expired, remove from cache
                        del _query_cache[key]
                
                # Cache miss, execute query
                logger.debug("Cache miss for %s", key)
                result = func(*args, **kwargs)
                _query_cache[key] = (result, time.time())
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def clear_cache(pattern: Optional[str] = None) -> None:
        """Clear query cache.
        
        Args:
            pattern: Optional pattern to match cache keys (clears all if None)
        """
        global _query_cache
        
        if pattern:
            keys_to_remove = [k for k in _query_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del _query_cache[key]
            logger.info("Cleared %d cache entries matching '%s'", len(keys_to_remove), pattern)
        else:
            _query_cache.clear()
            logger.info("Cleared all query cache")
    
    @staticmethod
    def get_cache_stats() -> dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(_query_cache)
        expired_entries = sum(
            1 for _, timestamp in _query_cache.values()
            if time.time() - timestamp >= _cache_ttl
        )
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "cache_ttl": _cache_ttl,
        }

