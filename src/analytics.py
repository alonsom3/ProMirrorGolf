"""
Analytics Module - Frame-level metrics, flaw deltas, similarity evolution
Exports data to CSV/HTML for analysis
"""

import csv
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class SwingAnalytics:
    """
    Tracks and exports swing analysis data for performance monitoring and improvement tracking
    """
    
    def __init__(self, output_dir: str = "./data/analytics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Frame-level metrics tracking
        self.frame_metrics = deque(maxlen=1000)  # Last 1000 frames
        
        # Swing-level tracking
        self.swing_history = []  # All swings in current session
        
        # Flaw evolution tracking
        self.flaw_history = []  # Track flaw changes over time
        
        # Similarity evolution
        self.similarity_history = []  # Track pro match similarity over time
        
        logger.info(f"Analytics initialized (output: {self.output_dir})")
    
    def log_frame(self, frame_number: int, processing_time_ms: float, 
                  swing_detected: bool, pose_quality: float = 0.0):
        """
        Log frame-level metrics
        
        Args:
            frame_number: Frame index
            processing_time_ms: Processing time in milliseconds
            swing_detected: Whether swing was detected
            pose_quality: Quality score of pose detection (0-1)
        """
        self.frame_metrics.append({
            'timestamp': datetime.now().isoformat(),
            'frame_number': frame_number,
            'processing_time_ms': processing_time_ms,
            'swing_detected': swing_detected,
            'pose_quality': pose_quality
        })
    
    def log_swing(self, swing_id: str, metrics: Dict, flaw_analysis: Dict, 
                  pro_match: Dict, shot_data: Dict):
        """
        Log complete swing analysis
        
        Args:
            swing_id: Unique swing identifier
            metrics: Extracted metrics
            flaw_analysis: Flaw detection results
            pro_match: Pro match information
            shot_data: Shot data from launch monitor
        """
        swing_entry = {
            'swing_id': swing_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'overall_score': flaw_analysis.get('overall_score', 0),
            'flaw_count': flaw_analysis.get('flaw_count', 0),
            'top_flaws': [f['metric'] for f in flaw_analysis.get('flaws', [])[:3]],
            'pro_match': pro_match.get('golfer_name', 'Unknown'),
            'similarity_score': pro_match.get('similarity_score', 0),
            'shot_data': shot_data
        }
        
        self.swing_history.append(swing_entry)
        
        # Track flaw evolution
        self._track_flaw_evolution(swing_entry)
        
        # Track similarity evolution
        self._track_similarity_evolution(swing_entry)
        
        logger.debug(f"Logged swing: {swing_id}")
    
    def _track_flaw_evolution(self, swing_entry: Dict):
        """Track how flaws change over time"""
        current_flaws = {f['metric']: f['severity'] 
                       for f in swing_entry.get('metrics', {}).items()}
        
        if self.flaw_history:
            # Compare with previous swing
            prev_flaws = self.flaw_history[-1].get('flaws', {})
            deltas = {}
            for metric, severity in current_flaws.items():
                prev_severity = prev_flaws.get(metric, 0)
                deltas[metric] = severity - prev_severity
            
            swing_entry['flaw_deltas'] = deltas
        
        self.flaw_history.append({
            'swing_id': swing_entry['swing_id'],
            'timestamp': swing_entry['timestamp'],
            'flaws': current_flaws,
            'overall_score': swing_entry['overall_score']
        })
    
    def _track_similarity_evolution(self, swing_entry: Dict):
        """Track how pro match similarity changes over time"""
        self.similarity_history.append({
            'swing_id': swing_entry['swing_id'],
            'timestamp': swing_entry['timestamp'],
            'pro_name': swing_entry['pro_match'],
            'similarity_score': swing_entry['similarity_score']
        })
    
    def export_csv(self, filename: Optional[str] = None) -> str:
        """
        Export swing history to CSV
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to exported CSV file
        """
        if not filename:
            filename = f"swing_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        csv_path = self.output_dir / filename
        
        if not self.swing_history:
            logger.warning("No swing data to export")
            return str(csv_path)
        
        # Write CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'swing_id', 'timestamp', 'overall_score', 'flaw_count',
                'pro_match', 'similarity_score', 'ball_speed', 'club_speed',
                'carry_distance', 'hip_rotation', 'shoulder_rotation', 'x_factor',
                'spine_angle', 'tempo_ratio'
            ])
            
            writer.writeheader()
            
            for swing in self.swing_history:
                metrics = swing.get('metrics', {})
                shot_data = swing.get('shot_data', {})
                
                writer.writerow({
                    'swing_id': swing['swing_id'],
                    'timestamp': swing['timestamp'],
                    'overall_score': swing.get('overall_score', 0),
                    'flaw_count': swing.get('flaw_count', 0),
                    'pro_match': swing.get('pro_match', 'Unknown'),
                    'similarity_score': swing.get('similarity_score', 0),
                    'ball_speed': shot_data.get('BallSpeed', 0),
                    'club_speed': shot_data.get('ClubSpeed', 0),
                    'carry_distance': shot_data.get('CarryDistance', 0),
                    'hip_rotation': metrics.get('hip_rotation_top', 0),
                    'shoulder_rotation': metrics.get('shoulder_rotation_top', 0),
                    'x_factor': metrics.get('x_factor', 0),
                    'spine_angle': metrics.get('spine_angle_address', 0),
                    'tempo_ratio': metrics.get('tempo_ratio', 0)
                })
        
        logger.info(f"Exported {len(self.swing_history)} swings to {csv_path}")
        return str(csv_path)
    
    def export_html_dashboard(self, filename: Optional[str] = None) -> str:
        """
        Export HTML dashboard with charts and statistics
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to exported HTML file
        """
        if not filename:
            filename = f"analytics_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html_path = self.output_dir / filename
        
        # Generate HTML with embedded charts (using Chart.js via CDN)
        html_content = self._generate_dashboard_html()
        
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Exported dashboard to {html_path}")
        return str(html_path)
    
    def _generate_dashboard_html(self) -> str:
        """Generate HTML dashboard with embedded JavaScript charts"""
        # Prepare data for charts
        timestamps = [s['timestamp'] for s in self.swing_history]
        scores = [s['overall_score'] for s in self.swing_history]
        similarities = [s['similarity_score'] for s in self.swing_history]
        flaw_counts = [s['flaw_count'] for s in self.swing_history]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ProMirrorGolf Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #0a0a0a; color: #e0e0e0; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #ff4444; }}
        .chart-container {{ background: #141414; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        canvas {{ max-height: 400px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #141414; padding: 20px; border-radius: 8px; }}
        .stat-value {{ font-size: 2em; color: #4caf50; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ProMirrorGolf Analytics Dashboard</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="stats">
            <div class="stat-card">
                <div>Total Swings</div>
                <div class="stat-value">{len(self.swing_history)}</div>
            </div>
            <div class="stat-card">
                <div>Avg Score</div>
                <div class="stat-value">{sum(scores)/len(scores) if scores else 0:.1f}</div>
            </div>
            <div class="stat-card">
                <div>Avg Similarity</div>
                <div class="stat-value">{sum(similarities)/len(similarities) if similarities else 0:.1f}%</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Swing Score Over Time</h2>
            <canvas id="scoreChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h2>Pro Match Similarity</h2>
            <canvas id="similarityChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h2>Flaw Count Trend</h2>
            <canvas id="flawChart"></canvas>
        </div>
    </div>
    
    <script>
        const timestamps = {json.dumps(timestamps)};
        const scores = {json.dumps(scores)};
        const similarities = {json.dumps(similarities)};
        const flawCounts = {json.dumps(flaw_counts)};
        
        // Score chart
        new Chart(document.getElementById('scoreChart'), {{
            type: 'line',
            data: {{
                labels: timestamps,
                datasets: [{{
                    label: 'Overall Score',
                    data: scores,
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{ beginAtZero: true, max: 100 }}
                }}
            }}
        }});
        
        // Similarity chart
        new Chart(document.getElementById('similarityChart'), {{
            type: 'line',
            data: {{
                labels: timestamps,
                datasets: [{{
                    label: 'Similarity %',
                    data: similarities,
                    borderColor: '#ff4444',
                    backgroundColor: 'rgba(255, 68, 68, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{ beginAtZero: true, max: 100 }}
                }}
            }}
        }});
        
        // Flaw count chart
        new Chart(document.getElementById('flawChart'), {{
            type: 'bar',
            data: {{
                labels: timestamps,
                datasets: [{{
                    label: 'Flaw Count',
                    data: flawCounts,
                    backgroundColor: '#ff9800'
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        return html
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for current session"""
        if not self.swing_history:
            return {"total_swings": 0}
        
        scores = [s['overall_score'] for s in self.swing_history]
        similarities = [s['similarity_score'] for s in self.swing_history]
        flaw_counts = [s['flaw_count'] for s in self.swing_history]
        
        return {
            "total_swings": len(self.swing_history),
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "avg_similarity": sum(similarities) / len(similarities) if similarities else 0,
            "avg_flaw_count": sum(flaw_counts) / len(flaw_counts) if flaw_counts else 0,
            "improvement_trend": self._calculate_improvement_trend()
        }
    
    def _calculate_improvement_trend(self) -> str:
        """Calculate if user is improving over time"""
        if len(self.swing_history) < 2:
            return "insufficient_data"
        
        recent_scores = [s['overall_score'] for s in self.swing_history[-5:]]
        earlier_scores = [s['overall_score'] for s in self.swing_history[:5]]
        
        if len(recent_scores) < 2 or len(earlier_scores) < 2:
            return "insufficient_data"
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        earlier_avg = sum(earlier_scores) / len(earlier_scores)
        
        diff = recent_avg - earlier_avg
        
        if diff > 2:
            return "improving"
        elif diff < -2:
            return "declining"
        else:
            return "stable"
    
    def clear_session(self):
        """Clear current session data"""
        self.swing_history.clear()
        self.flaw_history.clear()
        self.similarity_history.clear()
        self.frame_metrics.clear()
        logger.info("Analytics session cleared")
    
    def get_best_swings(self, limit: int = 5) -> List[Dict]:
        """
        Get best swings based on overall score
        
        Args:
            limit: Number of best swings to return
            
        Returns:
            List of swing dictionaries sorted by score (highest first)
        """
        if not self.swing_history:
            return []
        
        sorted_swings = sorted(
            self.swing_history,
            key=lambda x: x.get('overall_score', 0),
            reverse=True
        )
        return sorted_swings[:limit]
    
    def get_improvement_trends(self, metric_name: str, days: int = 30) -> Dict:
        """
        Get improvement trends for a specific metric over time
        
        Args:
            metric_name: Name of metric to track
            days: Number of days to look back
            
        Returns:
            Dictionary with trend data
        """
        if not self.swing_history:
            return {'trend': 'insufficient_data', 'data': []}
        
        # Filter swings by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_swings = [
            s for s in self.swing_history
            if datetime.fromisoformat(s['timestamp']) >= cutoff_date
        ]
        
        if len(recent_swings) < 2:
            return {'trend': 'insufficient_data', 'data': []}
        
        # Extract metric values
        metric_values = []
        for swing in recent_swings:
            if metric_name == 'overall_score':
                value = swing.get('overall_score', 0)
            elif metric_name == 'similarity_score':
                value = swing.get('similarity_score', 0)
            else:
                value = swing.get('metrics', {}).get(metric_name, 0)
            
            metric_values.append({
                'timestamp': swing['timestamp'],
                'value': value
            })
        
        # Calculate trend
        if len(metric_values) >= 2:
            first_half = metric_values[:len(metric_values)//2]
            second_half = metric_values[len(metric_values)//2:]
            
            first_avg = sum(m['value'] for m in first_half) / len(first_half)
            second_avg = sum(m['value'] for m in second_half) / len(second_half)
            
            if second_avg > first_avg * 1.05:
                trend = 'improving'
            elif second_avg < first_avg * 0.95:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'metric': metric_name,
            'trend': trend,
            'data': metric_values,
            'first_half_avg': first_avg if len(metric_values) >= 2 else 0,
            'second_half_avg': second_avg if len(metric_values) >= 2 else 0
        }
    
    def compare_sessions(self, session1_id: str, session2_id: str) -> Dict:
        """
        Compare two sessions
        
        Args:
            session1_id: First session identifier
            session2_id: Second session identifier
            
        Returns:
            Comparison dictionary
        """
        # This would need session tracking - simplified version
        swings1 = [s for s in self.swing_history if s.get('session_id') == session1_id]
        swings2 = [s for s in self.swing_history if s.get('session_id') == session2_id]
        
        if not swings1 or not swings2:
            return {'error': 'One or both sessions not found'}
        
        scores1 = [s.get('overall_score', 0) for s in swings1]
        scores2 = [s.get('overall_score', 0) for s in swings2]
        
        return {
            'session1': {
                'id': session1_id,
                'swing_count': len(swings1),
                'avg_score': sum(scores1) / len(scores1) if scores1 else 0,
                'max_score': max(scores1) if scores1 else 0
            },
            'session2': {
                'id': session2_id,
                'swing_count': len(swings2),
                'avg_score': sum(scores2) / len(scores2) if scores2 else 0,
                'max_score': max(scores2) if scores2 else 0
            },
            'improvement': (sum(scores2) / len(scores2) if scores2 else 0) - (sum(scores1) / len(scores1) if scores1 else 0)
        }

