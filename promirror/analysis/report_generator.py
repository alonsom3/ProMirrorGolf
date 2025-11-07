"""
Report Generator
Creates comprehensive visual analysis reports with comparisons
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
from pathlib import Path
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive swing analysis reports including:
    - Side-by-side comparison videos
    - Metrics comparison charts
    - Text reports with recommendations
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ReportGenerator initialized: {output_dir}")
    
    async def create_report(self, swing_id: str, user_video_path: str,
                           pro_match: Dict, user_metrics: Dict,
                           flaw_analysis: Dict, shot_data: Dict) -> Dict:
        """
        Create complete analysis report.
        
        Args:
            swing_id: Unique identifier for this swing
            user_video_path: Path to user's swing video
            pro_match: Matched professional swing data
            user_metrics: User's swing metrics
            flaw_analysis: Detected flaws and recommendations
            shot_data: Launch monitor data
            
        Returns:
            Dictionary with report file paths and data
        """
        logger.info(f"Generating report for {swing_id}...")
        
        report_dir = self.output_dir / swing_id
        report_dir.mkdir(exist_ok=True)
        
        # Create comparison video
        comparison_path = None
        if pro_match.get('video_path'):
            comparison_path = await self._create_comparison_video(
                user_video_path, pro_match['video_path'], report_dir
            )
        
        # Create metrics chart
        chart_path = self._create_metrics_chart(
            user_metrics, pro_match.get('metrics', {}), report_dir
        )
        
        # Create text report
        text_path = self._create_text_report(
            swing_id, user_metrics, flaw_analysis, shot_data, pro_match, report_dir
        )
        
        report = {
            'swing_id': swing_id,
            'report_dir': str(report_dir),
            'comparison_video': str(comparison_path) if comparison_path else None,
            'metrics_chart': str(chart_path),
            'text_report': str(text_path),
            'overall_score': flaw_analysis.get('overall_score', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Report generated: {report_dir}")
        return report
    
    async def _create_comparison_video(self, user_path: str, pro_path: str,
                                      output_dir: Path) -> Optional[Path]:
        """Create side-by-side comparison video"""
        output_path = output_dir / "comparison.mp4"
        
        if not Path(user_path).exists():
            logger.warning(f"User video not found: {user_path}")
            return None
        
        if not Path(pro_path).exists():
            logger.warning(f"Pro video not found: {pro_path}")
            return None
        
        try:
            # Load videos
            user_cap = cv2.VideoCapture(user_path)
            pro_cap = cv2.VideoCapture(pro_path)
            
            # Get properties
            width = int(user_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(user_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(user_cap.get(cv2.CAP_PROP_FPS)) or 30
            
            # Create output video (side-by-side)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width * 2, height))
            
            frame_count = 0
            while True:
                ret1, user_frame = user_cap.read()
                ret2, pro_frame = pro_cap.read()
                
                if not ret1 or not ret2:
                    break
                
                # Resize pro to match user
                pro_frame = cv2.resize(pro_frame, (width, height))
                
                # Add labels
                cv2.putText(user_frame, "YOUR SWING", (20, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                cv2.putText(pro_frame, "PRO SWING", (20, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)
                
                # Combine side-by-side
                combined = np.hstack([user_frame, pro_frame])
                out.write(combined)
                frame_count += 1
            
            user_cap.release()
            pro_cap.release()
            out.release()
            
            logger.info(f"Comparison video created: {frame_count} frames")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating comparison video: {e}")
            return None
    
    def _create_metrics_chart(self, user_metrics: Dict, pro_metrics: Dict,
                             output_dir: Path) -> Path:
        """Create bar chart comparing metrics"""
        output_path = output_dir / "metrics_chart.png"
        
        # Select key metrics to display
        display_metrics = [
            'hip_rotation', 'shoulder_rotation', 'x_factor', 
            'tempo_ratio', 'weight_transfer', 'club_speed'
        ]
        
        # Filter to available metrics
        available_metrics = [m for m in display_metrics 
                           if m in user_metrics and m in pro_metrics]
        
        if not available_metrics:
            logger.warning("No common metrics to compare")
            # Create empty chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, "No metrics available for comparison", 
                   ha='center', va='center', fontsize=16)
            ax.axis('off')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path
        
        # Get values
        user_vals = [user_metrics.get(m, 0) for m in available_metrics]
        pro_vals = [pro_metrics.get(m, 0) for m in available_metrics]
        
        # Create chart
        x = np.arange(len(available_metrics))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars1 = ax.bar(x - width/2, user_vals, width, label='Your Swing', 
                      color='steelblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, pro_vals, width, label='Pro Swing', 
                      color='darkgreen', alpha=0.8)
        
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title('Swing Metrics Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace('_', ' ').title() for m in available_metrics], 
                          rotation=45, ha='right')
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Metrics chart created: {output_path}")
        return output_path
    
    def _create_text_report(self, swing_id: str, metrics: Dict,
                           flaws: Dict, shot_data: Dict, pro: Dict,
                           output_dir: Path) -> Path:
        """Create text-based report"""
        output_path = output_dir / "report.txt"
        
        lines = [
            "=" * 70,
            f"SWING ANALYSIS REPORT - {swing_id}",
            "=" * 70,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"OVERALL SCORE: {flaws.get('overall_score', 0):.1f}/100",
            f"Matched Pro: {pro.get('golfer_name', 'Unknown')}",
            f"Similarity: {pro.get('similarity_score', 0):.1f}%",
            "",
            "LAUNCH MONITOR DATA:",
            "-" * 70,
            f"Ball Speed: {shot_data.get('ball_speed', 0):.1f} mph",
            f"Club Speed: {shot_data.get('club_speed', 0):.1f} mph",
            f"Launch Angle: {shot_data.get('launch_angle', 0):.1f}°",
            f"Carry Distance: {shot_data.get('carry_distance', 0):.1f} yards",
            f"Spin Rate: {shot_data.get('spin_rate', 0):.0f} rpm",
            "",
            "SWING METRICS:",
            "-" * 70,
        ]
        
        # Add metrics
        for metric, value in sorted(metrics.items()):
            display_name = metric.replace('_', ' ').title()
            lines.append(f"{display_name}: {value:.2f}")
        
        # Add flaws
        lines.extend([
            "",
            "DETECTED ISSUES:",
            "-" * 70
        ])
        
        flaw_list = flaws.get('flaws', [])
        if flaw_list:
            for i, flaw in enumerate(flaw_list[:5], 1):  # Top 5 flaws
                lines.extend([
                    f"{i}. {flaw['metric_display']}",
                    f"   Issue: {flaw['issue'].replace('_', ' ').title()}",
                    f"   Your value: {flaw['value']:.2f}",
                    f"   Ideal range: {flaw.get('ideal_min', 'N/A')}-{flaw.get('ideal_max', 'N/A')}",
                    f"   Severity: {flaw['severity_level'].upper()}",
                    f"   Recommendation: {flaw['recommendation']}",
                    ""
                ])
        else:
            lines.append("✓ No significant issues detected - Great swing!")
        
        lines.extend([
            "",
            "=" * 70,
            "Report generated by ProMirrorGolf Swing Analysis System",
            "=" * 70
        ])
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Text report created: {output_path}")
        return output_path


# Test function
def test_report_generator():
    """Test the report generator"""
    import asyncio
    
    async def run_test():
        generator = ReportGenerator('./test_reports')
        
        # Sample data
        swing_id = f"test_swing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        user_metrics = {
            'hip_rotation': 42,
            'shoulder_rotation': 95,
            'x_factor': 48,
            'tempo_ratio': 3.0,
            'weight_transfer': 0.09,
            'club_speed': 105
        }
        pro_match = {
            'golfer_name': 'Adam Scott',
            'similarity_score': 87.5,
            'metrics': {
                'hip_rotation': 42,
                'shoulder_rotation': 95,
                'x_factor': 48,
                'tempo_ratio': 3.2,
                'weight_transfer': 0.09,
                'club_speed': 112
            },
            'video_path': None
        }
        flaw_analysis = {
            'overall_score': 82.0,
            'flaws': [
                {
                    'metric': 'tempo_ratio',
                    'metric_display': 'Tempo Ratio',
                    'value': 3.0,
                    'ideal_min': 2.5,
                    'ideal_max': 3.5,
                    'issue': 'within_range',
                    'severity_level': 'minor',
                    'recommendation': 'Good tempo overall'
                }
            ]
        }
        shot_data = {
            'ball_speed': 155,
            'club_speed': 105,
            'launch_angle': 12.5,
            'carry_distance': 268,
            'spin_rate': 2450
        }
        
        # Generate report
        report = await generator.create_report(
            swing_id=swing_id,
            user_video_path='./test_video.mp4',
            pro_match=pro_match,
            user_metrics=user_metrics,
            flaw_analysis=flaw_analysis,
            shot_data=shot_data
        )
        
        print(f"\n✓ Report generated successfully!")
        print(f"Report directory: {report['report_dir']}")
        print(f"Text report: {report['text_report']}")
        print(f"Metrics chart: {report['metrics_chart']}")
        print(f"Overall score: {report['overall_score']}/100")
    
    asyncio.run(run_test())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_report_generator()
