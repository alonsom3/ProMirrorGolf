"""
Batch Video Processor - Process multiple videos in queue
"""

import asyncio
import logging
from typing import List, Dict, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Processing status for batch items"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchItem:
    """Single item in batch processing queue"""
    video_id: str
    dtl_path: str
    face_path: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress: float = 0.0
    result: Optional[Dict] = None
    error: Optional[str] = None
    swing_id: Optional[str] = None


class BatchProcessor:
    """
    Batch video processor for processing multiple videos in queue
    Supports progress tracking, cancellation, and result aggregation
    """
    
    def __init__(self, controller, quality_mode: str = "balanced", downsample_factor: int = 1):
        """
        Initialize batch processor
        
        Args:
            controller: SwingAIController instance
            quality_mode: Quality mode for processing
            downsample_factor: Downsample factor for processing
        """
        self.controller = controller
        self.quality_mode = quality_mode
        self.downsample_factor = downsample_factor
        
        self.queue: List[BatchItem] = []
        self.current_item: Optional[BatchItem] = None
        self.processing = False
        self.cancelled = False
        
        # Callbacks
        self.on_item_started: Optional[Callable[[BatchItem], None]] = None
        self.on_item_progress: Optional[Callable[[BatchItem, float], None]] = None
        self.on_item_completed: Optional[Callable[[BatchItem], None]] = None
        self.on_item_failed: Optional[Callable[[BatchItem, str], None]] = None
        self.on_batch_completed: Optional[Callable[[List[BatchItem]], None]] = None
    
    def add_video(self, dtl_path: str, face_path: str, video_id: Optional[str] = None) -> str:
        """
        Add video to processing queue
        
        Args:
            dtl_path: Path to DTL video
            face_path: Path to Face-on video
            video_id: Optional video identifier (generated if None)
            
        Returns:
            Video ID
        """
        if not video_id:
            video_id = f"batch_{Path(dtl_path).stem}_{len(self.queue)}"
        
        item = BatchItem(
            video_id=video_id,
            dtl_path=dtl_path,
            face_path=face_path,
            status=ProcessingStatus.PENDING
        )
        
        self.queue.append(item)
        logger.info(f"Added video to batch queue: {video_id}")
        return video_id
    
    def add_videos(self, video_pairs: List[tuple]) -> List[str]:
        """
        Add multiple videos to queue
        
        Args:
            video_pairs: List of (dtl_path, face_path) tuples
            
        Returns:
            List of video IDs
        """
        video_ids = []
        for dtl_path, face_path in video_pairs:
            video_id = self.add_video(dtl_path, face_path)
            video_ids.append(video_id)
        return video_ids
    
    async def process_all(self):
        """
        Process all videos in queue
        
        Returns:
            List of completed BatchItems
        """
        if self.processing:
            logger.warning("Batch processing already in progress")
            return []
        
        self.processing = True
        self.cancelled = False
        
        completed_items = []
        
        try:
            for item in self.queue:
                if self.cancelled:
                    item.status = ProcessingStatus.CANCELLED
                    break
                
                if item.status == ProcessingStatus.COMPLETED:
                    completed_items.append(item)
                    continue
                
                # Process item
                self.current_item = item
                item.status = ProcessingStatus.PROCESSING
                item.progress = 0.0
                
                if self.on_item_started:
                    self.on_item_started(item)
                
                try:
                    # Set up progress callback
                    def progress_callback(progress: float, message: str):
                        item.progress = progress
                        if self.on_item_progress:
                            self.on_item_progress(item, progress)
                    
                    # Temporarily set progress callback
                    original_callback = self.controller.on_progress_update
                    self.controller.on_progress_update = progress_callback
                    
                    # Process video
                    result = await self.controller.process_uploaded_videos(
                        item.dtl_path,
                        item.face_path,
                        downsample_factor=self.downsample_factor,
                        quality_mode=self.quality_mode
                    )
                    
                    # Restore original callback
                    self.controller.on_progress_update = original_callback
                    
                    if result.get('success'):
                        item.status = ProcessingStatus.COMPLETED
                        item.result = result
                        item.swing_id = result.get('swing_id')
                        item.progress = 1.0
                        completed_items.append(item)
                        
                        if self.on_item_completed:
                            self.on_item_completed(item)
                    else:
                        item.status = ProcessingStatus.FAILED
                        item.error = result.get('error', 'Unknown error')
                        
                        if self.on_item_failed:
                            self.on_item_failed(item, item.error)
                
                except Exception as e:
                    item.status = ProcessingStatus.FAILED
                    item.error = str(e)
                    logger.error(f"Error processing batch item {item.video_id}: {e}")
                    
                    if self.on_item_failed:
                        self.on_item_failed(item, item.error)
        
        finally:
            self.processing = False
            self.current_item = None
            
            if self.on_batch_completed:
                self.on_batch_completed(completed_items)
        
        return completed_items
    
    def cancel(self):
        """Cancel batch processing"""
        self.cancelled = True
        logger.info("Batch processing cancelled")
    
    def clear_queue(self):
        """Clear processing queue"""
        self.queue.clear()
        self.current_item = None
        logger.info("Batch queue cleared")
    
    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        status_counts = {
            ProcessingStatus.PENDING: 0,
            ProcessingStatus.PROCESSING: 0,
            ProcessingStatus.COMPLETED: 0,
            ProcessingStatus.FAILED: 0,
            ProcessingStatus.CANCELLED: 0
        }
        
        for item in self.queue:
            status_counts[item.status] += 1
        
        return {
            'total': len(self.queue),
            'pending': status_counts[ProcessingStatus.PENDING],
            'processing': status_counts[ProcessingStatus.PROCESSING],
            'completed': status_counts[ProcessingStatus.COMPLETED],
            'failed': status_counts[ProcessingStatus.FAILED],
            'cancelled': status_counts[ProcessingStatus.CANCELLED],
            'current_item': self.current_item.video_id if self.current_item else None
        }
    
    def get_summary_report(self) -> Dict:
        """Generate summary report for completed batch"""
        completed = [item for item in self.queue if item.status == ProcessingStatus.COMPLETED]
        failed = [item for item in self.queue if item.status == ProcessingStatus.FAILED]
        
        total_swings = len(completed)
        total_frames = sum(
            item.result.get('frames_processed', 0) 
            for item in completed 
            if item.result
        )
        
        return {
            'total_videos': len(self.queue),
            'completed': len(completed),
            'failed': len(failed),
            'total_swings_detected': total_swings,
            'total_frames_processed': total_frames,
            'success_rate': len(completed) / len(self.queue) * 100 if self.queue else 0,
            'completed_items': [
                {
                    'video_id': item.video_id,
                    'swing_id': item.swing_id,
                    'frames_processed': item.result.get('frames_processed', 0) if item.result else 0
                }
                for item in completed
            ],
            'failed_items': [
                {
                    'video_id': item.video_id,
                    'error': item.error
                }
                for item in failed
            ]
        }

