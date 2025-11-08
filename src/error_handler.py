"""
Error Handler - User-friendly error messages and recovery suggestions
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# User-friendly error message mappings
ERROR_MESSAGES = {
    "camera_not_found": {
        "title": "Camera Not Detected",
        "message": "Unable to detect camera. Please check your camera connections.",
        "suggestions": [
            "Ensure cameras are connected via USB",
            "Check camera permissions in Windows settings",
            "Try unplugging and reconnecting the cameras",
            "Restart the application",
            "Verify camera IDs in config.json match your system"
        ],
        "technical": "Camera initialization failed - check camera IDs and permissions"
    },
    
    "video_processing_failed": {
        "title": "Video Processing Failed",
        "message": "Unable to process the uploaded videos. The videos may be corrupted or in an unsupported format.",
        "suggestions": [
            "Try a different video file",
            "Ensure video format is MP4, AVI, or MOV",
            "Check that both DTL and Face videos are provided",
            "Verify videos are not corrupted",
            "Ensure videos have sufficient frames (>10 frames)"
        ],
        "technical": "Video processing error - check video format and file integrity"
    },
    
    "video_format_unsupported": {
        "title": "Unsupported Video Format",
        "message": "The video format is not supported. Please convert to a supported format.",
        "suggestions": [
            "Convert video to MP4 format",
            "Use H.264 codec for best compatibility",
            "Ensure video resolution is at least 480p",
            "Check video file is not corrupted"
        ],
        "technical": "Unsupported video codec or format"
    },
    
    "frame_count_mismatch": {
        "title": "Video Length Mismatch",
        "message": "The DTL and Face videos have different lengths. Processing will use the shorter video.",
        "suggestions": [
            "Record videos with the same duration",
            "Trim videos to match lengths",
            "Ensure both videos start at the same time",
            "This warning is safe to ignore - processing will continue"
        ],
        "technical": "DTL and Face videos have different frame counts"
    },
    
    "session_start_failed": {
        "title": "Session Start Failed",
        "message": "Unable to start a new session. Please check your configuration.",
        "suggestions": [
            "Verify camera connections",
            "Check config.json settings",
            "Ensure database files are accessible",
            "Restart the application",
            "Check available disk space"
        ],
        "technical": "Session initialization failed"
    },
    
    "database_error": {
        "title": "Database Error",
        "message": "Unable to access the database. Data may not be saved.",
        "suggestions": [
            "Check database file permissions",
            "Ensure sufficient disk space",
            "Verify database files are not locked by another process",
            "Restart the application",
            "Check database file paths in config.json"
        ],
        "technical": "Database access error"
    },
    
    "mlm2pro_connection_failed": {
        "title": "MLM2Pro Connection Failed",
        "message": "Unable to connect to MLM2Pro launch monitor. Live shot data will not be available.",
        "suggestions": [
            "Ensure MLM2Pro is powered on",
            "Check connector path in config.json",
            "Verify OpenGolfSim connector is running",
            "Check network connection",
            "Video upload mode will work without MLM2Pro"
        ],
        "technical": "MLM2Pro connector initialization failed"
    },
    
    "pose_detection_failed": {
        "title": "Pose Detection Failed",
        "message": "Unable to detect pose in video frames. The video may not contain a clear view of the golfer.",
        "suggestions": [
            "Ensure golfer is clearly visible in videos",
            "Check lighting conditions",
            "Verify camera angles are correct (DTL and Face-on)",
            "Try a different video with better visibility",
            "Ensure golfer is in frame throughout the swing"
        ],
        "technical": "MediaPipe pose detection failed - no landmarks detected"
    },
    
    "timeout_error": {
        "title": "Processing Timeout",
        "message": "Video processing took too long and timed out. The video may be too long or complex.",
        "suggestions": [
            "Try using shorter video clips (<2 minutes)",
            "Use speed mode for faster processing",
            "Increase downsample factor to process fewer frames",
            "Check system resources (CPU, memory)",
            "Close other applications to free resources"
        ],
        "technical": "Video processing exceeded timeout limit (600 seconds)"
    },
    
    "export_failed": {
        "title": "Export Failed",
        "message": "Unable to export the video or report. The file may be in use or the path is invalid.",
        "suggestions": [
            "Check file path is valid and writable",
            "Ensure file is not open in another application",
            "Verify sufficient disk space",
            "Try a different file location",
            "Check file permissions"
        ],
        "technical": "File export error"
    },
    
    "general_error": {
        "title": "An Error Occurred",
        "message": "An unexpected error occurred. Please try again or contact support if the problem persists.",
        "suggestions": [
            "Try the operation again",
            "Restart the application",
            "Check the log file (promirror.log) for details",
            "Ensure all dependencies are installed",
            "Verify configuration file is valid"
        ],
        "technical": "Unexpected error"
    }
}


class ErrorHandler:
    """Handles user-friendly error messages and recovery suggestions"""
    
    @staticmethod
    def get_error_info(error_type: str, technical_details: Optional[str] = None) -> Dict:
        """
        Get user-friendly error information
        
        Args:
            error_type: Error type key from ERROR_MESSAGES
            technical_details: Optional technical error message
            
        Returns:
            Dictionary with title, message, suggestions, and technical details
        """
        error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["general_error"]).copy()
        
        if technical_details:
            error_info["technical"] = f"{error_info.get('technical', '')}: {technical_details}"
        
        return error_info
    
    @staticmethod
    def format_error_message(error_type: str, technical_details: Optional[str] = None) -> str:
        """
        Format error message for display
        
        Args:
            error_type: Error type key
            technical_details: Optional technical details
            
        Returns:
            Formatted error message string
        """
        error_info = ErrorHandler.get_error_info(error_type, technical_details)
        
        message = f"{error_info['message']}\n\n"
        message += "Suggestions:\n"
        for i, suggestion in enumerate(error_info['suggestions'], 1):
            message += f"{i}. {suggestion}\n"
        
        return message
    
    @staticmethod
    def get_suggestions(error_type: str) -> List[str]:
        """Get list of suggestions for an error type"""
        error_info = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["general_error"])
        return error_info.get("suggestions", [])
    
    @staticmethod
    def detect_error_type(exception: Exception, context: Optional[str] = None) -> str:
        """
        Detect error type from exception
        
        Args:
            exception: Exception object
            context: Optional context string
            
        Returns:
            Error type key
        """
        error_str = str(exception).lower()
        error_type = str(type(exception).__name__).lower()
        
        # Camera errors
        if "camera" in error_str or "camera" in error_type or context:
            return "camera_not_found"
        
        # Video errors
        if "video" in error_str or "video" in error_type or "video" in (context or ""):
            if "format" in error_str or "codec" in error_str:
                return "video_format_unsupported"
            if "frame" in error_str and "mismatch" in error_str:
                return "frame_count_mismatch"
            return "video_processing_failed"
        
        # Database errors
        if "database" in error_str or "sqlite" in error_str or "db" in error_type:
            return "database_error"
        
        # Timeout errors
        if "timeout" in error_str or "timeout" in error_type:
            return "timeout_error"
        
        # Pose detection errors
        if "pose" in error_str or "landmark" in error_str:
            return "pose_detection_failed"
        
        # MLM2Pro errors
        if "mlm2pro" in error_str or "launch" in error_str or "connector" in error_str:
            return "mlm2pro_connection_failed"
        
        # Export errors
        if "export" in error_str or "file" in error_str and "write" in error_str:
            return "export_failed"
        
        # Session errors
        if "session" in error_str:
            return "session_start_failed"
        
        return "general_error"

