# File: swing_ai_core.py

import asyncio
import logging
import uuid
import time
import cv2
from typing import Dict, Optional, List, Tuple
from .camera_manager import DualCameraManager
from .pose_analyzer import PoseAnalyzer
from .database import SwingDatabase
from .style_matcher import StyleMatcher
from .report_generator import ReportGenerator
from .metrics_extractor import MetricsExtractor
from .flaw_detector import FlawDetector
from .mlm2pro_listener import LaunchMonitorListener
from .video_processor import VideoProcessor
from .ai_coach import AICoach
from .gamification import GamificationSystem
import numpy as np

logger = logging.getLogger(__name__)

class SwingAIController:
    """Main controller for Swing AI - Production-ready with MLM2Pro integration and video upload"""

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = None
        self.camera_manager = None
        self.pose_analyzer = None
        self.db = None
        self.style_matcher = None
        self.report_generator = None
        self.metrics_extractor = None
        self.flaw_detector = None
        self.launch_monitor = None
        self.video_processor = None
        self.ai_coach = None
        self.gamification = None
        
        self.session_active = False
        self.processing_cancelled = False  # Flag for cancel button
        self.processing_start_time = None  # For ETA calculation
        self.current_user = None
        self.session_name = None
        self.current_session_id = None
        self.current_club = "Driver"
        self.on_swing_detected = None  # Callback for UI updates
        
        # Video upload mode
        self.use_video_upload = False
        self.pending_shot_data = None  # Shot data waiting for swing analysis
        
        self.load_config()

    def load_config(self):
        import json
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
            logger.info("SwingAIController config loaded")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {}

    async def initialize(self):
        """Initialize all AI components"""
        logger.info("Initializing Swing AI modules...")

        self.camera_manager = DualCameraManager(self.config)
        self.pose_analyzer = PoseAnalyzer(self.config)
        self.metrics_extractor = MetricsExtractor()
        self.flaw_detector = FlawDetector()
        self.video_processor = VideoProcessor()
        
        db_path = self.config.get("database", {}).get("swing_db_path", "./data/swings.db")
        self.db = SwingDatabase(db_path)
        pro_db_path = self.config.get("database", {}).get("pro_db_path", "./data/pro_swings.db")
        self.style_matcher = StyleMatcher(pro_db_path)
        output_dir = self.config.get("reports", {}).get("output_dir", "./data/reports")
        self.report_generator = ReportGenerator(output_dir)
        
        # Initialize AI Coach and Gamification
        self.ai_coach = AICoach(self.db)
        self.gamification = GamificationSystem(self.db)
        
        # Initialize MLM2Pro listener if configured
        mlm2pro_cfg = self.config.get("mlm2pro", {})
        if mlm2pro_cfg.get("connector_path"):
            try:
                self.launch_monitor = LaunchMonitorListener(
                    connector_path=mlm2pro_cfg.get("connector_path"),
                    connector_type=mlm2pro_cfg.get("connector_type", "opengolfsim")
                )
                logger.info("MLM2Pro listener initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize MLM2Pro listener: {e}")

        logger.info("All Swing AI components initialized")

    async def start_session(self, user_id: str, session_name: str, use_video_upload: bool = False):
        """Start a practice session (live camera or video upload mode)"""
        self.current_user = user_id
        self.session_name = session_name
        self.session_active = True
        self.use_video_upload = use_video_upload

        logger.info(f"Starting session for {user_id} - {session_name} (mode: {'video_upload' if use_video_upload else 'live_camera'})")

        if use_video_upload:
            # Video upload mode - don't start cameras
            logger.info("Video upload mode - cameras disabled")
        else:
            # Live camera mode
            if not self.camera_manager:
                self.camera_manager = DualCameraManager(self.config)
            await self.camera_manager.start_buffering()

        # Start MLM2Pro listener if available (skip in video upload mode)
        if use_video_upload:
            logger.info("Video upload mode active - MLM2Pro connector skipped")
        elif self.launch_monitor:
            try:
                self.launch_monitor.start_listening()
                logger.info("MLM2Pro listener started")
            except Exception as e:
                logger.warning(f"Failed to start MLM2Pro listener: {e}")

        # Create DB session
        self.current_session_id = self.db.create_session(user_id, session_name)
        logger.info(f"Database session created: {self.current_session_id}")

        # Start monitoring swings
        if use_video_upload:
            # For video upload, monitoring is triggered manually via process_uploaded_videos
            pass
        else:
            asyncio.create_task(self._monitor_swings())

    async def stop_session(self):
        """Stop current session safely with timeout handling"""
        if not self.session_active:
            logger.warning("No active session to stop")
            return

        logger.info("Stopping session...")
        self.session_active = False
        
        # Stop cameras if in live mode (with timeout)
        if self.camera_manager and not self.use_video_upload:
            try:
                await asyncio.wait_for(self.camera_manager.stop_buffering(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Camera stop timed out, continuing...")
            except Exception as e:
                logger.warning(f"Error stopping cameras: {e}")
        
        # Stop MLM2Pro listener (skip in video upload mode)
        if not self.use_video_upload and self.launch_monitor:
            try:
                self.launch_monitor.stop_listening()
            except Exception as e:
                logger.warning(f"Error stopping MLM2Pro listener: {e}")
        
        # Release video processor if in upload mode (with timeout protection)
        if self.use_video_upload and self.video_processor:
            try:
                self.video_processor.release()
            except Exception as e:
                logger.warning(f"Error releasing video processor: {e}")
        
        logger.info("Session stopped successfully")

    async def _monitor_swings(self):
        """Monitor frames for swing detection"""
        logger.info("Monitoring swings...")
        
        last_swing_time = 0
        min_shot_interval = self.config.get("processing", {}).get("min_shot_interval", 3.0)

        while self.session_active:
            # Grab latest frames from camera manager
            frames = await self.camera_manager.get_latest_frames()
            if not frames or frames[0] is None or frames[1] is None:
                await asyncio.sleep(0.01)
                continue

            dtl_frame, face_frame = frames

            # Run pose analysis
            pose_data = await self.pose_analyzer.analyze(dtl_frame, face_frame)

            # Check if swing detected (with debouncing)
            current_time = time.time()
            
            if pose_data.get("swing_detected") and (current_time - last_swing_time) >= min_shot_interval:
                logger.info("Swing detected! Analyzing...")
                last_swing_time = current_time
                
                # Analyze swing with full pipeline
                swing_data = await self._analyze_swing(pose_data)
                
                # Clear pose buffer after processing
                self.pose_analyzer.clear_buffer()
                
                # Save swing to database
                swing_id = str(uuid.uuid4())
                swing_data['swing_id'] = swing_id
                
                self.db.save_swing(
                    session_id=self.current_session_id,
                    swing_id=swing_id,
                    swing_metrics=swing_data.get("metrics", {}),
                    shot_data=swing_data.get("shot_data", {}),
                    video_paths={"dtl": "", "face": ""},  # Will be populated when videos are saved
                    report_path="",  # Will be populated when report is generated
                    pro_match_id=swing_data.get("pro_match", {}).get("pro_id", ""),
                    flaw_analysis=swing_data.get("flaw_analysis", {})
                )

                # Trigger callback in GUI if set
                if hasattr(self, "on_swing_detected") and callable(self.on_swing_detected):
                    self.on_swing_detected(swing_data)

            await asyncio.sleep(0.01)  # Small delay to avoid CPU spinning

    async def _analyze_swing(self, pose_data):
        """
        Full swing analysis pipeline:
        1. Extract metrics from pose data
        2. Detect flaws
        3. Find pro match
        4. Return complete swing data
        """
        logger.info("Starting full swing analysis...")
        
        # Get FPS from config
        fps = self.config.get("cameras", {}).get("fps", 60)
        
        # Step 1: Extract metrics from pose data
        metrics = self.metrics_extractor.extract_metrics_from_pose(pose_data, fps)
        logger.info(f"Extracted metrics: {metrics}")
        
        # Step 2: Detect flaws
        flaw_analysis = self.flaw_detector.detect_flaws(metrics)
        overall_score = flaw_analysis.get("overall_score", 75.0)
        logger.info(f"Flaw analysis complete: {flaw_analysis.get('flaw_count', 0)} flaws, score: {overall_score}")
        
        # Step 3: Find pro match
        club_type = getattr(self, 'current_club', 'Driver')  # Default to Driver
        pro_match = await self.style_matcher.find_best_match(metrics, club_type)
        logger.info(f"Pro match found: {pro_match.get('golfer_name', 'Unknown')} (similarity: {pro_match.get('similarity_score', 0):.2f})")
        
        # Step 4: Get shot data (from launch monitor if available, otherwise use defaults)
        shot_data = self._get_shot_data(metrics)
        
        # Step 5: Build complete swing data
        swing_data = {
            "swing_id": None,  # Will be set by caller
            "metrics": metrics,
            "shot_data": shot_data,
            "flaw_analysis": flaw_analysis,
            "pro_match": pro_match,
            "overall_score": overall_score,
            "pose_data": pose_data  # Include for potential future use
        }
        
        logger.info("Swing analysis complete")
        return swing_data
    
    def _get_shot_data(self, metrics: Dict) -> Dict:
        """
        Get shot data from launch monitor or estimate from metrics
        
        Priority:
        1. Pending shot data from MLM2Pro (if available)
        2. Latest shot from MLM2Pro listener
        3. Estimate from metrics
        """
        # Check for pending shot data (from MLM2Pro)
        if self.pending_shot_data:
            shot_data = self.pending_shot_data.copy()
            self.pending_shot_data = None  # Clear after use
            logger.info("Using pending shot data from MLM2Pro")
            return shot_data
        
        # Try to get latest shot from MLM2Pro listener (non-blocking)
        if self.launch_monitor and self.launch_monitor.is_listening:
            try:
                # Check if there's a shot in the queue (non-blocking)
                if not self.launch_monitor.shot_queue.empty():
                    shot_data = self.launch_monitor.shot_queue.get_nowait()
                    logger.info("Using shot data from MLM2Pro listener")
                    return shot_data
            except Exception as e:
                logger.debug(f"No shot data available from MLM2Pro: {e}")
        
        # Fallback: estimate from metrics or use defaults
        shot_data = {
            "ClubSpeed": metrics.get("club_speed", 95.0),  # mph
            "BallSpeed": metrics.get("ball_speed", 140.0),  # mph (estimated from club speed)
            "LaunchAngle": 12.0,  # degrees (typical driver)
            "SpinRate": 2500,  # rpm
            "CarryDistance": 220,  # yards (estimated)
            "TotalDistance": 250  # yards (estimated)
        }
        
        # Estimate ball speed from club speed if not available
        if "ball_speed" not in metrics and "club_speed" in metrics:
            shot_data["BallSpeed"] = shot_data["ClubSpeed"] * 1.45  # Typical smash factor
        
        return shot_data
    
    async def process_uploaded_videos(self, dtl_path: str, face_path: str, downsample_factor: int = 1, 
                                     quality_mode: str = "balanced") -> Dict:
        """
        Process uploaded videos for swing analysis
        
        Args:
            dtl_path: Path to down-the-line video
            face_path: Path to face-on video
            downsample_factor: Process every Nth frame (1=all frames, 2=every other, etc.)
            
        Returns:
            Dictionary with processing results
        """
        if not self.session_active:
            return {"success": False, "error": "No active session"}
        
        logger.info(f"VIDEO UPLOAD MODE: Processing uploaded videos")
        logger.info(f"  DTL: {dtl_path}")
        logger.info(f"  Face: {face_path}")
        logger.info(f"  Downsample factor: {downsample_factor} (process every {downsample_factor} frame(s))")
        
        # Load and validate videos
        result = self.video_processor.load_videos(dtl_path, face_path)
        if not result['success']:
            return {"success": False, "errors": result['errors']}
        
        # Check frame count alignment
        dtl_frames = result['dtl_info'].get('frames', 0)
        face_frames = result['face_info'].get('frames', 0)
        frame_diff = abs(dtl_frames - face_frames)
        
        if frame_diff > 0:
            logger.warning(f"Frame count mismatch: DTL={dtl_frames}, Face={face_frames}, Diff={frame_diff} frames")
            logger.warning(f"  Using shorter video length: {min(dtl_frames, face_frames)} frames")
        
        # Log video info
        logger.info(f"Video properties:")
        logger.info(f"  DTL: {dtl_frames} frames @ {result['dtl_info'].get('fps', 0):.1f} fps, "
                   f"{result['dtl_info'].get('width', 0)}x{result['dtl_info'].get('height', 0)}")
        logger.info(f"  Face: {face_frames} frames @ {result['face_info'].get('fps', 0):.1f} fps, "
                   f"{result['face_info'].get('width', 0)}x{result['face_info'].get('height', 0)}")
        
        # Calculate total frames to process (with downsampling)
        total_frames_to_process = (min(dtl_frames, face_frames) // downsample_factor) + (1 if min(dtl_frames, face_frames) % downsample_factor else 0)
        
        logger.info(f"Processing {total_frames_to_process} frame pairs (downsampled from {min(dtl_frames, face_frames)})...")
        
        # Use generator for lazy loading with parallel extraction
        frame_generator = self.video_processor.get_frame_generator(
            downsample_factor=downsample_factor, 
            use_parallel=True
        )
        
        # Analyze frames with threaded processing for UI responsiveness
        all_pose_data = []
        processed_count = 0
        processing_times = []
        best_swing_so_far = None  # For progressive display
        
        # Process frames in batches for better performance
        batch_size = 10  # Process 10 frames before checking for cancellation
        
        frame_batch = []
        for frame_info in frame_generator:
            # Check if session was stopped or cancelled
            if not self.session_active or self.processing_cancelled:
                logger.warning("Processing cancelled by user")
                return {"success": False, "error": "Processing cancelled - session stopped"}
            
            frame_batch.append(frame_info)
            
            # Process batch when full or at end
            if len(frame_batch) >= batch_size:
                batch_results = await self._process_frame_batch_parallel(
                    frame_batch, processing_times, quality_mode
                )
                all_pose_data.extend(batch_results)
                processed_count += len(frame_batch)
                
                # Update best swing for progressive display
                if batch_results:
                    current_best = max(batch_results, key=lambda x: len(x.get("dtl_poses", [])))
                    if not best_swing_so_far or len(current_best.get("dtl_poses", [])) > len(best_swing_so_far.get("dtl_poses", [])):
                        best_swing_so_far = current_best
                        # Progressive callback for preview
                        if hasattr(self, 'on_progressive_result') and callable(self.on_progressive_result):
                            self.on_progressive_result(best_swing_so_far, processed_count, total_frames_to_process)
                
                # Calculate ETA
                elapsed_time = time.time() - self.processing_start_time
                if processed_count > 0 and elapsed_time > 0:
                    avg_time_per_frame = elapsed_time / processed_count
                    remaining_frames = total_frames_to_process - processed_count
                    eta_seconds = remaining_frames * avg_time_per_frame
                    eta_minutes = int(eta_seconds // 60)
                    eta_secs = int(eta_seconds % 60)
                    eta_str = f"{eta_minutes}m {eta_secs}s" if eta_minutes > 0 else f"{eta_secs}s"
                else:
                    eta_str = "Calculating..."
                
                # Update progress callback (thread-safe) with ETA
                if hasattr(self, 'on_progress_update') and callable(self.on_progress_update):
                    progress = processed_count / total_frames_to_process
                    avg_time = np.mean(processing_times[-batch_size:]) if processing_times else 0
                    self.on_progress_update(
                        progress, 
                        f"Frame {processed_count}/{total_frames_to_process} | Avg: {avg_time:.1f}ms | ETA: {eta_str}"
                    )
                
                frame_batch = []
        
        # Process remaining frames
        if frame_batch and not self.processing_cancelled:
            batch_results = await self._process_frame_batch_parallel(
                frame_batch, processing_times, quality_mode
            )
            all_pose_data.extend(batch_results)
            processed_count += len(frame_batch)
            
            # Update best swing
            if batch_results:
                current_best = max(batch_results, key=lambda x: len(x.get("dtl_poses", [])))
                if not best_swing_so_far or len(current_best.get("dtl_poses", [])) > len(best_swing_so_far.get("dtl_poses", [])):
                    best_swing_so_far = current_best
        
        # Log performance statistics
        if processing_times:
            avg_time = np.mean(processing_times)
            max_time = np.max(processing_times)
            min_time = np.min(processing_times)
            p95_time = np.percentile(processing_times, 95)
            
            logger.info(f"Frame processing complete: {processed_count} frames processed, {len(all_pose_data)} swings detected")
            logger.info(f"Performance: avg={avg_time:.1f}ms, min={min_time:.1f}ms, max={max_time:.1f}ms, p95={p95_time:.1f}ms")
            
            if avg_time > 100:
                logger.warning(f"Average processing time ({avg_time:.1f}ms) exceeds target (100ms)")
        
        if not all_pose_data:
            return {"success": False, "error": "No swings detected in videos"}
        
        # Use the best swing (most complete pose data)
        best_pose_data = max(all_pose_data, key=lambda x: len(x.get("dtl_poses", [])))
        logger.info(f"Selected best swing with {len(best_pose_data.get('dtl_poses', []))} pose frames")
        
        # Run full analysis pipeline (same as live mode)
        logger.info("Running full analysis pipeline (metrics, flaws, pro matching)...")
        swing_data = await self._analyze_swing(best_pose_data)
        
        # Save swing to database
        swing_id = str(uuid.uuid4())
        swing_data['swing_id'] = swing_id
        
        self.db.save_swing(
            session_id=self.current_session_id,
            swing_id=swing_id,
            swing_metrics=swing_data.get("metrics", {}),
            shot_data=swing_data.get("shot_data", {}),
            video_paths={"dtl": dtl_path, "face": face_path},
            report_path="",
            pro_match_id=swing_data.get("pro_match", {}).get("pro_id", ""),
            flaw_analysis=swing_data.get("flaw_analysis", {})
        )
        
        logger.info(f"Swing saved to database: {swing_id}")
        
        # Trigger callback
        if self.on_swing_detected:
            self.on_swing_detected(swing_data)
        
        return {
            "success": True,
            "swing_id": swing_id,
            "swing_data": swing_data,
            "frames_processed": processed_count,
            "swings_detected": len(all_pose_data)
        }
    
    def cancel_processing(self):
        """Cancel ongoing video processing"""
        self.processing_cancelled = True
        logger.info("Processing cancellation requested by user")
    
    async def _process_frame_batch_parallel(self, frame_batch: List[Tuple], processing_times: List[float], 
                                           quality_mode: str = "balanced") -> List[Dict]:
        """
        Process a batch of frames with parallel pose detection for faster analysis
        
        Args:
            frame_batch: List of (frame_index, dtl_frame, face_frame) tuples
            processing_times: List to append processing times to
            quality_mode: "speed", "balanced", or "quality"
            
        Returns:
            List of pose data dictionaries for frames with detected swings
        """
        batch_results = []
        
        # Process DTL and Face poses in parallel for each frame
        async def process_frame_parallel(frame_idx, dtl_frame, face_frame):
            start_time = time.time()
            
            # Adjust processing based on quality mode
            if quality_mode == "speed":
                # Speed mode: resize frames smaller for faster processing
                target_width = 480
            elif quality_mode == "quality":
                # Quality mode: keep original size or minimal resize
                target_width = 1280
            else:  # balanced
                target_width = 640
            
            # Resize if needed
            if dtl_frame.shape[1] > target_width:
                scale = target_width / dtl_frame.shape[1]
                new_height = int(dtl_frame.shape[0] * scale)
                dtl_frame = cv2.resize(dtl_frame, (target_width, new_height), interpolation=cv2.INTER_LINEAR)
                face_frame = cv2.resize(face_frame, (target_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # Create parallel tasks for DTL and Face pose detection
            dtl_task = asyncio.create_task(self._analyze_dtl_pose(dtl_frame))
            face_task = asyncio.create_task(self._analyze_face_pose(face_frame))
            
            # Wait for both to complete
            dtl_result, face_result = await asyncio.gather(dtl_task, face_task)
            
            # Combine results
            pose_data = self._combine_pose_results(dtl_result, face_result, dtl_frame, face_frame)
            
            elapsed_ms = (time.time() - start_time) * 1000
            processing_times.append(elapsed_ms)
            
            if elapsed_ms > 100:
                logger.warning(f"Frame {frame_idx} processing took {elapsed_ms:.1f}ms (target: <100ms)")
            
            return pose_data
        
        # Process all frames in batch
        tasks = [process_frame_parallel(frame_idx, dtl_frame, face_frame) 
                 for frame_idx, dtl_frame, face_frame in frame_batch]
        results = await asyncio.gather(*tasks)
        
        # Filter for detected swings
        for pose_data in results:
            if pose_data.get("swing_detected"):
                batch_results.append(pose_data)
        
        return batch_results
    
    async def _analyze_dtl_pose(self, dtl_frame):
        """Analyze DTL frame pose (for parallel processing)"""
        if dtl_frame is None:
            return None
        # Use pose analyzer's DTL pose detector
        dtl_rgb = cv2.cvtColor(dtl_frame, cv2.COLOR_BGR2RGB)
        result = self.pose_analyzer.pose_dtl.process(dtl_rgb)
        return self.pose_analyzer._extract_landmarks(result)
    
    async def _analyze_face_pose(self, face_frame):
        """Analyze Face frame pose (for parallel processing)"""
        if face_frame is None:
            return None
        # Use pose analyzer's Face pose detector
        face_rgb = cv2.cvtColor(face_frame, cv2.COLOR_BGR2RGB)
        result = self.pose_analyzer.pose_face.process(face_rgb)
        return self.pose_analyzer._extract_landmarks(result)
    
    def _combine_pose_results(self, dtl_landmarks, face_landmarks, dtl_frame, face_frame):
        """Combine DTL and Face pose results into full pose data"""
        # This mimics the pose_analyzer.analyze() method but with pre-processed landmarks
        swing_detected = bool(dtl_landmarks) and bool(face_landmarks)
        
        if dtl_landmarks:
            self.pose_analyzer.dtl_pose_buffer.append(dtl_landmarks)
        if face_landmarks:
            self.pose_analyzer.face_pose_buffer.append(face_landmarks)
        
        dtl_poses = list(self.pose_analyzer.dtl_pose_buffer)
        face_poses = list(self.pose_analyzer.face_pose_buffer)
        
        events = {}
        if len(dtl_poses) >= 30 and swing_detected:
            events = self.pose_analyzer._detect_swing_events(dtl_poses)
        
        return {
            "swing_detected": swing_detected,
            "dtl_poses": dtl_poses,
            "face_poses": face_poses,
            "events": events,
            "dtl_landmarks": dtl_landmarks,
            "face_landmarks": face_landmarks
        }
    
    def get_mlm2pro_status(self) -> Dict:
        """Get MLM2Pro connection status"""
        if not self.launch_monitor:
            return {
                "connected": False,
                "status": "not_configured",
                "message": "MLM2Pro not configured"
            }
        
        status = self.launch_monitor.get_status()
        return {
            "connected": status.get("is_listening", False),
            "connector_running": status.get("connector_running", False),
            "last_shot_time": status.get("last_shot_time", 0),
            "pending_shots": status.get("pending_shots", 0),
            "status": "connected" if status.get("is_listening") else "disconnected"
        }
