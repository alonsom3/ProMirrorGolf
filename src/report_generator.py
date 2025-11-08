"""
Report Generator - Creates visual analysis reports
Overlay System - Displays results in GSPro
"""

import cv2
import numpy as np
from typing import Dict, List
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive swing analysis reports
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ReportGenerator initialized: {output_dir}")
    
    async def create_report(self, swing_id: str, user_videos: Dict, pro_match: Dict,
                           swing_metrics: Dict, flaw_analysis: Dict, 
                           shot_data: Dict, pose_data: Dict) -> Dict:
        """
        Create a comprehensive swing analysis report
        
        Returns:
            Dictionary with report data and file paths
        """
        logger.info(f"Generating report for {swing_id}...")
        
        report_dir = self.output_dir / swing_id
        report_dir.mkdir(exist_ok=True)
        
        # 1. Create side-by-side comparison video
        comparison_video_path = await self._create_comparison_video(
            user_videos, pro_match, report_dir
        )
        
        # 2. Create overlay video with skeleton
        overlay_video_path = await self._create_overlay_video(
            user_videos, pose_data, report_dir
        )
        
        # 3. Create metrics visualization
        metrics_image_path = self._create_metrics_chart(
            swing_metrics, pro_match['metrics'], report_dir
        )
        
        # 4. Create flaw visualization
        flaw_image_path = self._create_flaw_diagram(
            flaw_analysis, report_dir
        )
        
        # 5. Generate text report
        text_report_path = self._create_text_report(
            swing_id, swing_metrics, flaw_analysis, shot_data, pro_match, report_dir
        )
        
        # 6. Create JSON data for overlay display
        overlay_data_path = self._create_overlay_data(
            swing_id, swing_metrics, flaw_analysis, shot_data, pro_match,
            comparison_video_path, report_dir
        )
        
        report = {
            'swing_id': swing_id,
            'path': str(report_dir),
            'comparison_video': str(comparison_video_path),
            'overlay_video': str(overlay_video_path),
            'metrics_chart': str(metrics_image_path),
            'flaw_diagram': str(flaw_image_path),
            'text_report': str(text_report_path),
            'overlay_data': str(overlay_data_path),
            'swing_metrics': swing_metrics,
            'flaw_analysis': flaw_analysis,
            'shot_data': shot_data,
            'pro_match': pro_match
        }
        
        logger.info(f"Report generated: {report_dir}")
        
        return report
    
    async def _create_comparison_video(self, user_videos: Dict, pro_match: Dict, 
                                       output_dir: Path) -> Path:
        """
        Create side-by-side comparison video (user vs pro)
        """
        output_path = output_dir / "comparison.mp4"
        
        # Load user videos
        user_dtl = cv2.VideoCapture(user_videos['dtl'])
        
        # Load pro video
        if pro_match.get('video_dtl_path'):
            pro_dtl = cv2.VideoCapture(pro_match['video_dtl_path'])
        else:
            # No pro video available, create placeholder
            logger.warning("No pro video available for comparison")
            return output_path
        
        # Get dimensions
        width = int(user_dtl.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(user_dtl.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(user_dtl.get(cv2.CAP_PROP_FPS))
        
        # Create output video (side-by-side)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width * 2, height))
        
        # Synchronize and combine frames
        while True:
            ret1, user_frame = user_dtl.read()
            ret2, pro_frame = pro_dtl.read()
            
            if not ret1 or not ret2:
                break
            
            # Resize pro frame to match user frame
            pro_frame = cv2.resize(pro_frame, (width, height))
            
            # Add labels
            user_frame = self._add_label(user_frame, "YOUR SWING", (10, 30))
            pro_frame = self._add_label(pro_frame, f"{pro_match['golfer_name']}", (10, 30))
            
            # Combine side-by-side
            combined = np.hstack([user_frame, pro_frame])
            
            out.write(combined)
        
        user_dtl.release()
        pro_dtl.release()
        out.release()
        
        logger.info(f"Comparison video created: {output_path}")
        
        return output_path
    
    async def _create_overlay_video(self, user_videos: Dict, pose_data: Dict,
                                    output_dir: Path) -> Path:
        """
        Create video with skeleton overlay
        """
        output_path = output_dir / "skeleton_overlay.mp4"
        
        cap = cv2.VideoCapture(user_videos['dtl'])
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        frame_idx = 0
        dtl_poses = pose_data['dtl_poses']
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Draw skeleton if pose available
            if frame_idx < len(dtl_poses) and dtl_poses[frame_idx]['landmarks']:
                frame = self._draw_skeleton(frame, dtl_poses[frame_idx]['landmarks'])
            
            out.write(frame)
            frame_idx += 1
        
        cap.release()
        out.release()
        
        logger.info(f"Overlay video created: {output_path}")
        
        return output_path
    
    def _draw_skeleton(self, frame: np.ndarray, landmarks: Dict) -> np.ndarray:
        """Draw skeleton on frame"""
        height, width = frame.shape[:2]
        
        # MediaPipe connections
        connections = [
            (11, 12), (11, 13), (13, 15),  # Left arm
            (12, 14), (14, 16),  # Right arm
            (11, 23), (12, 24),  # Torso
            (23, 24), (23, 25), (25, 27),  # Left leg
            (24, 26), (26, 28)  # Right leg
        ]
        
        # Draw connections
        for start_idx, end_idx in connections:
            if start_idx in landmarks and end_idx in landmarks:
                start_lm = landmarks[start_idx]
                end_lm = landmarks[end_idx]
                
                start_point = (int(start_lm['x'] * width), int(start_lm['y'] * height))
                end_point = (int(end_lm['x'] * width), int(end_lm['y'] * height))
                
                cv2.line(frame, start_point, end_point, (0, 255, 0), 2)
        
        # Draw joints
        for idx, landmark in landmarks.items():
            point = (int(landmark['x'] * width), int(landmark['y'] * height))
            cv2.circle(frame, point, 4, (0, 0, 255), -1)
        
        return frame
    
    def _add_label(self, frame: np.ndarray, text: str, position: tuple) -> np.ndarray:
        """Add text label to frame"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, text, position, font, 1, (255, 255, 255), 2, cv2.LINE_AA)
        return frame
    
    def _create_metrics_chart(self, user_metrics: Dict, pro_metrics: Dict, 
                             output_dir: Path) -> Path:
        """Create radar/bar chart comparing metrics"""
        output_path = output_dir / "metrics_comparison.png"
        
        # Key metrics to display
        display_metrics = [
            'hip_rotation_top',
            'shoulder_rotation_top',
            'x_factor',
            'tempo_ratio',
            'weight_transfer'
        ]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(display_metrics))
        width = 0.35
        
        user_values = [user_metrics.get(m, 0) for m in display_metrics]
        pro_values = [pro_metrics.get(m, 0) for m in display_metrics]
        
        ax.bar(x - width/2, user_values, width, label='Your Swing', color='steelblue')
        ax.bar(x + width/2, pro_values, width, label='Pro Swing', color='darkgreen')
        
        ax.set_ylabel('Value')
        ax.set_title('Swing Metrics Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace('_', ' ').title() for m in display_metrics], rotation=45)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        return output_path
    
    def _create_flaw_diagram(self, flaw_analysis: Dict, output_dir: Path) -> Path:
        """Create visual diagram of detected flaws"""
        output_path = output_dir / "flaw_analysis.png"
        
        flaws = flaw_analysis.get('flaws', [])
        
        if not flaws:
            # No flaws - create "excellent" message
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "Excellent Swing!\\nNo Major Flaws Detected", 
                   ha='center', va='center', fontsize=24, color='green')
            ax.axis('off')
            plt.savefig(output_path, dpi=150)
            plt.close()
            return output_path
        
        # Create flaw visualization
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Show top 5 flaws
        top_flaws = flaws[:5]
        
        y_pos = np.arange(len(top_flaws))
        severities = [f['severity'] for f in top_flaws]
        labels = [f"{f['metric'].replace('_', ' ').title()}\\n({f['issue']})" for f in top_flaws]
        
        colors = ['red' if s > 0.7 else 'orange' if s > 0.4 else 'yellow' for s in severities]
        
        ax.barh(y_pos, severities, color=colors)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.set_xlabel('Severity')
        ax.set_title('Detected Swing Flaws (Top 5)')
        ax.set_xlim(0, 1)
        
        # Add recommendations
        for i, flaw in enumerate(top_flaws):
            ax.text(0.95, i, flaw['recommendation'][:40] + '...', 
                   va='center', ha='right', fontsize=8, style='italic')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        return output_path
    
    def _create_text_report(self, swing_id: str, swing_metrics: Dict, 
                           flaw_analysis: Dict, shot_data: Dict, 
                           pro_match: Dict, output_dir: Path) -> Path:
        """Create formatted text report"""
        output_path = output_dir / "report.txt"
        
        report_lines = [
            "=" * 60,
            f"SWING ANALYSIS REPORT - {swing_id}",
            "=" * 60,
            "",
            f"Overall Score: {flaw_analysis.get('overall_score', 0):.1f}/100",
            f"Matched Pro: {pro_match.get('golfer_name', 'Unknown')}",
            f"Similarity: {pro_match.get('similarity_score', 0):.1f}%",
            "",
            "SHOT DATA:",
            "-" * 60,
            f"Ball Speed: {shot_data.get('BallSpeed', 0):.1f} mph",
            f"Club Speed: {shot_data.get('ClubSpeed', 0):.1f} mph",
            f"Launch Angle: {shot_data.get('LaunchAngle', 0):.1f}°",
            f"Spin Rate: {shot_data.get('SpinRate', 0):.0f} rpm",
            f"Carry Distance: {shot_data.get('CarryDistance', 0):.1f} yards",
            f"Total Distance: {shot_data.get('TotalDistance', 0):.1f} yards",
            "",
            "SWING METRICS:",
            "-" * 60
        ]
        
        for metric, value in swing_metrics.items():
            report_lines.append(f"{metric.replace('_', ' ').title()}: {value:.2f}")
        
        report_lines.extend([
            "",
            "DETECTED FLAWS:",
            "-" * 60
        ])
        
        flaws = flaw_analysis.get('flaws', [])
        if flaws:
            for i, flaw in enumerate(flaws, 1):
                report_lines.extend([
                    f"{i}. {flaw['metric'].replace('_', ' ').title()}",
                    f"   Issue: {flaw['issue']}",
                    f"   Severity: {flaw['severity']:.2f}",
                    f"   Your value: {flaw['value']:.2f}",
                    f"   Ideal range: {flaw['ideal_min']:.2f} - {flaw['ideal_max']:.2f}",
                    f"   Recommendation: {flaw['recommendation']}",
                    ""
                ])
        else:
            report_lines.append("No significant flaws detected - Great swing!")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        return output_path
    
    def _create_overlay_data(self, swing_id: str, swing_metrics: Dict, 
                            flaw_analysis: Dict, shot_data: Dict, 
                            pro_match: Dict, comparison_video: Path, 
                            output_dir: Path) -> Path:
        """Create JSON data for overlay display"""
        output_path = output_dir / "overlay_data.json"
        
        # Top 3 flaws for quick display
        top_flaws = flaw_analysis.get('flaws', [])[:3]
        
        overlay_data = {
            'swing_id': swing_id,
            'overall_score': flaw_analysis.get('overall_score', 0),
            'matched_pro': pro_match.get('golfer_name', 'Unknown'),
            'comparison_video': str(comparison_video),
            'shot_data': {
                'ball_speed': shot_data.get('BallSpeed', 0),
                'club_speed': shot_data.get('ClubSpeed', 0),
                'launch_angle': shot_data.get('LaunchAngle', 0),
                'carry_distance': shot_data.get('CarryDistance', 0),
                'spin_rate': shot_data.get('SpinRate', 0)
            },
            'key_metrics': {
                'tempo': swing_metrics.get('tempo_ratio', 0),
                'x_factor': swing_metrics.get('x_factor', 0),
                'hip_rotation': swing_metrics.get('hip_rotation_top', 0)
            },
            'top_flaws': [
                {
                    'name': f['metric'].replace('_', ' ').title(),
                    'severity': f['severity'],
                    'recommendation': f['recommendation']
                } for f in top_flaws
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(overlay_data, f, indent=2)
        
        return output_path
    
    def create_comparison_report(self, swing1: Dict, swing2: Dict) -> Dict:
        """Compare two swings (e.g., before/after)"""
        # Implementation for swing-to-swing comparison
        pass

