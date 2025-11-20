"""Video export functionality with drawing overlays."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple, Callable

import cv2
import numpy as np
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


def render_drawings_on_frame(
    frame: np.ndarray,
    lines: list[Tuple[int, int, int, int, QColor, int]],
    overlay_text: str = "",
) -> np.ndarray:
    """Render drawings on a video frame.
    
    Args:
        frame: Input video frame (BGR format)
        lines: List of line tuples (x1, y1, x2, y2, color, width)
        overlay_text: Optional text overlay
        
    Returns:
        Frame with drawings rendered (BGR format)
    """
    result = frame.copy()
    
    # Render lines
    for x1, y1, x2, y2, color, width in lines:
        if color is None:
            continue
        
        # Convert QColor to BGR
        bgr_color = (color.blue(), color.green(), color.red())
        cv2.line(result, (int(x1), int(y1)), (int(x2), int(y2)), bgr_color, width)
    
    # Render overlay text
    if overlay_text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        color = (255, 255, 255)  # White
        (text_width, text_height), baseline = cv2.getTextSize(overlay_text, font, font_scale, thickness)
        
        # Add background rectangle for text
        cv2.rectangle(
            result,
            (10, 10),
            (20 + text_width, 30 + text_height),
            (0, 0, 0),
            -1,
        )
        
        # Add text
        cv2.putText(
            result,
            overlay_text,
            (15, 25 + text_height),
            font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
    
    return result


def export_video_with_drawings(
    video_path: Path,
    output_path: Path,
    lines: list[Tuple[int, int, int, int, QColor, int]],
    overlay_text: str = "",
    codec: str = "mp4v",
    fps: float = 60.0,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None,
    quality: Optional[int] = None,
    scale_factor: float = 1.0,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """Export video with drawings rendered on frames.
    
    Args:
        video_path: Input video file path
        output_path: Output video file path
        lines: List of line tuples (x1, y1, x2, y2, color, width)
        overlay_text: Optional text overlay
        codec: Video codec (mp4v, H264, HEVC)
        fps: Frames per second
        start_frame: Optional start frame (for trimming)
        end_frame: Optional end frame (for trimming)
        quality: Quality setting (1-100, affects compression)
        scale_factor: Scale factor for output resolution (1.0 = original, 0.5 = half size)
        
    Returns:
        True if export successful, False otherwise
    """
    if not video_path.exists():
        logger.error("Video file not found: %s", video_path)
        return False
    
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error("Failed to open video: %s", video_path)
            return False
        
        # Get video properties
        original_fps = cap.get(cv2.CAP_PROP_FPS) or fps
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(original_width * scale_factor)
        height = int(original_height * scale_factor)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if width <= 0 or height <= 0:
            logger.error("Invalid video dimensions: %dx%d", width, height)
            cap.release()
            return False
        
        # Determine frame range
        start = start_frame if start_frame is not None else 0
        end = end_frame if end_frame is not None else total_frames
        start = max(0, min(start, total_frames - 1))
        end = max(start + 1, min(end, total_frames))
        
        # Set up codec
        fourcc_map = {
            "mp4v": cv2.VideoWriter_fourcc(*"mp4v"),
            "H264": cv2.VideoWriter_fourcc(*"H264"),
            "HEVC": cv2.VideoWriter_fourcc(*"HEVC"),
            "X264": cv2.VideoWriter_fourcc(*"X264"),
            "XVID": cv2.VideoWriter_fourcc(*"XVID"),
        }
        
        fourcc = fourcc_map.get(codec.upper(), cv2.VideoWriter_fourcc(*"mp4v"))
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create video writer
        writer = cv2.VideoWriter(str(output_path), fourcc, original_fps, (width, height))
        if not writer.isOpened():
            logger.error("Failed to create video writer for %s (codec: %s)", output_path, codec)
            cap.release()
            return False
        
        # Seek to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        
        frames_written = 0
        current_frame = start
        total_frames_to_export = end - start
        
        while current_frame < end:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Render drawings on frame
            frame_with_drawings = render_drawings_on_frame(frame, lines, overlay_text)
            
            # Scale frame if needed
            if scale_factor != 1.0:
                frame_with_drawings = cv2.resize(
                    frame_with_drawings,
                    (width, height),
                    interpolation=cv2.INTER_AREA if scale_factor < 1.0 else cv2.INTER_LINEAR,
                )
            
            # Write frame
            writer.write(frame_with_drawings)
            frames_written += 1
            current_frame += 1
            
            # Update progress
            if progress_callback:
                progress_callback(frames_written, total_frames_to_export)
        
        writer.release()
        cap.release()
        
        if frames_written == 0:
            logger.error("No frames written to %s", output_path)
            if output_path.exists():
                output_path.unlink()
            return False
        
        logger.info(
            "Exported %d frames from %s to %s (codec: %s, fps: %.2f)",
            frames_written,
            video_path,
            output_path,
            codec,
            original_fps,
        )
        return True
        
    except Exception as e:
        logger.error("Error exporting video: %s", e, exc_info=True)
        return False


def export_dual_video_side_by_side(
    dtl_path: Optional[Path],
    face_path: Optional[Path],
    output_path: Path,
    dtl_lines: list[Tuple[int, int, int, int, QColor, int]],
    face_lines: list[Tuple[int, int, int, int, QColor, int]],
    dtl_overlay: str = "",
    face_overlay: str = "",
    codec: str = "mp4v",
    fps: float = 60.0,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None,
    scale_factor: float = 1.0,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """Export two videos side-by-side with drawings.
    
    Args:
        dtl_path: DTL video path (optional)
        face_path: Face video path (optional)
        output_path: Output video path
        dtl_lines: DTL drawing lines
        face_lines: Face drawing lines
        dtl_overlay: DTL overlay text
        face_overlay: Face overlay text
        codec: Video codec
        fps: Frames per second
        start_frame: Optional start frame
        end_frame: Optional end frame
        
    Returns:
        True if export successful, False otherwise
    """
    if not dtl_path and not face_path:
        logger.error("At least one video path required")
        return False
    
    try:
        # Open videos
        dtl_cap = None
        face_cap = None
        
        if dtl_path and dtl_path.exists():
            dtl_cap = cv2.VideoCapture(str(dtl_path))
            if not dtl_cap.isOpened():
                logger.warning("Failed to open DTL video: %s", dtl_path)
                dtl_cap = None
        
        if face_path and face_path.exists():
            face_cap = cv2.VideoCapture(str(face_path))
            if not face_cap.isOpened():
                logger.warning("Failed to open face video: %s", face_path)
                face_cap = None
        
        if not dtl_cap and not face_cap:
            logger.error("No valid videos to export")
            return False
        
        # Get video properties
        if dtl_cap:
            fps = dtl_cap.get(cv2.CAP_PROP_FPS) or fps
            dtl_width = int(dtl_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            dtl_height = int(dtl_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            dtl_total = int(dtl_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        else:
            dtl_width = dtl_height = dtl_total = 0
        
        if face_cap:
            face_fps = face_cap.get(cv2.CAP_PROP_FPS) or fps
            face_width = int(face_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            face_height = int(face_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            face_total = int(face_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = face_fps  # Use face FPS if DTL not available
        else:
            face_width = face_height = face_total = 0
        
        # Determine output dimensions
        if dtl_cap and face_cap:
            # Side-by-side: match heights, sum widths
            target_height = max(dtl_height, face_height)
            dtl_scale = target_height / dtl_height if dtl_height > 0 else 1.0
            face_scale = target_height / face_height if face_height > 0 else 1.0
            output_width = int((dtl_width * dtl_scale + face_width * face_scale) * scale_factor)
            output_height = int(target_height * scale_factor)
            total_frames = max(dtl_total, face_total)
        elif dtl_cap:
            output_width = int(dtl_width * scale_factor)
            output_height = int(dtl_height * scale_factor)
            total_frames = dtl_total
        else:
            output_width = int(face_width * scale_factor)
            output_height = int(face_height * scale_factor)
            total_frames = face_total
        
        if output_width <= 0 or output_height <= 0:
            logger.error("Invalid output dimensions: %dx%d", output_width, output_height)
            if dtl_cap:
                dtl_cap.release()
            if face_cap:
                face_cap.release()
            return False
        
        # Determine frame range
        start = start_frame if start_frame is not None else 0
        end = end_frame if end_frame is not None else total_frames
        start = max(0, min(start, total_frames - 1))
        end = max(start + 1, min(end, total_frames))
        
        # Set up codec
        fourcc_map = {
            "mp4v": cv2.VideoWriter_fourcc(*"mp4v"),
            "H264": cv2.VideoWriter_fourcc(*"H264"),
            "HEVC": cv2.VideoWriter_fourcc(*"HEVC"),
            "X264": cv2.VideoWriter_fourcc(*"X264"),
            "XVID": cv2.VideoWriter_fourcc(*"XVID"),
        }
        
        fourcc = fourcc_map.get(codec.upper(), cv2.VideoWriter_fourcc(*"mp4v"))
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create video writer
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (output_width, output_height))
        if not writer.isOpened():
            logger.error("Failed to create video writer for %s", output_path)
            if dtl_cap:
                dtl_cap.release()
            if face_cap:
                face_cap.release()
            return False
        
        # Seek to start frame
        if dtl_cap:
            dtl_cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        if face_cap:
            face_cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        
        frames_written = 0
        current_frame = start
        total_frames_to_export = end - start
        
        while current_frame < end:
            # Read frames
            dtl_frame = None
            face_frame = None
            
            if dtl_cap:
                ret, frame = dtl_cap.read()
                if ret:
                    dtl_frame = frame
            
            if face_cap:
                ret, frame = face_cap.read()
                if ret:
                    face_frame = frame
            
            if not dtl_frame and not face_frame:
                break
            
            # Render drawings
            if dtl_frame is not None:
                dtl_frame = render_drawings_on_frame(dtl_frame, dtl_lines, dtl_overlay)
            if face_frame is not None:
                face_frame = render_drawings_on_frame(face_frame, face_lines, face_overlay)
            
            # Combine frames side-by-side
            if dtl_frame is not None and face_frame is not None:
                # Resize to match heights
                dtl_h, dtl_w = dtl_frame.shape[:2]
                face_h, face_w = face_frame.shape[:2]
                target_h = max(dtl_h, face_h)
                
                dtl_scale = target_h / dtl_h
                face_scale = target_h / face_h
                
                dtl_resized = cv2.resize(dtl_frame, (int(dtl_w * dtl_scale), target_h))
                face_resized = cv2.resize(face_frame, (int(face_w * face_scale), target_h))
                
                combined = np.hstack([dtl_resized, face_resized])
            elif dtl_frame is not None:
                combined = dtl_frame
            elif face_frame is not None:
                combined = face_frame
            else:
                break
            
            # Apply scale factor if needed
            if scale_factor != 1.0:
                combined = cv2.resize(combined, (output_width, output_height),
                                    interpolation=cv2.INTER_AREA if scale_factor < 1.0 else cv2.INTER_LINEAR)
            
            # Write frame
            writer.write(combined)
            frames_written += 1
            current_frame += 1
            
            # Update progress
            if progress_callback:
                progress_callback(frames_written, total_frames_to_export)
        
        writer.release()
        if dtl_cap:
            dtl_cap.release()
        if face_cap:
            face_cap.release()
        
        if frames_written == 0:
            logger.error("No frames written to %s", output_path)
            if output_path.exists():
                output_path.unlink()
            return False
        
        logger.info(
            "Exported %d frames side-by-side to %s (codec: %s, fps: %.2f, size: %dx%d)",
            frames_written,
            output_path,
            codec,
            fps,
            output_width,
            output_height,
        )
        return True
        
    except Exception as e:
        logger.error("Error exporting dual video: %s", e, exc_info=True)
        return False

