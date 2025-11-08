"""
Export Manager - Export swings, sessions, and analytics to various formats
Supports PDF, CSV, HTML exports with annotations and branding
"""

import csv
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import webbrowser

logger = logging.getLogger(__name__)


class ExportManager:
    """
    Manages export of swing data, sessions, and analytics to various formats
    """
    
    def __init__(self, output_dir: str = "./data/exports"):
        """
        Initialize export manager
        
        Args:
            output_dir: Directory for exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ExportManager initialized (output: {self.output_dir})")
    
    def export_swing_csv(self, swing_data: Dict, output_path: Optional[str] = None) -> str:
        """
        Export swing data to CSV
        
        Args:
            swing_data: Swing data dictionary
            output_path: Optional output file path
            
        Returns:
            Path to exported CSV file
        """
        if not output_path:
            swing_id = swing_data.get('swing_id', 'swing')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"{swing_id}_{timestamp}.csv"
        else:
            output_path = Path(output_path)
        
        # Flatten swing data for CSV
        flat_data = {
            'swing_id': swing_data.get('swing_id', ''),
            'timestamp': swing_data.get('timestamp', ''),
            'session_id': swing_data.get('session_id', ''),
        }
        
        # Add metrics
        metrics = swing_data.get('metrics', {})
        for key, value in metrics.items():
            flat_data[f'metric_{key}'] = value
        
        # Add flaw analysis
        flaw_analysis = swing_data.get('flaw_analysis', {})
        flat_data['overall_score'] = flaw_analysis.get('overall_score', 0)
        flat_data['flaw_count'] = flaw_analysis.get('flaw_count', 0)
        
        # Add pro match
        pro_match = swing_data.get('pro_match', {})
        flat_data['pro_name'] = pro_match.get('golfer_name', '')
        flat_data['similarity_score'] = pro_match.get('similarity_score', 0)
        
        # Add shot data
        shot_data = swing_data.get('shot_data', {})
        for key, value in shot_data.items():
            flat_data[f'shot_{key}'] = value
        
        # Write CSV
        with open(output_path, 'w', newline='') as f:
            if flat_data:
                writer = csv.DictWriter(f, fieldnames=flat_data.keys())
                writer.writeheader()
                writer.writerow(flat_data)
        
        logger.info(f"Exported swing to CSV: {output_path}")
        return str(output_path)
    
    def export_session_csv(self, session_data: List[Dict], output_path: Optional[str] = None) -> str:
        """
        Export session data (multiple swings) to CSV
        
        Args:
            session_data: List of swing data dictionaries
            output_path: Optional output file path
            
        Returns:
            Path to exported CSV file
        """
        if not output_path:
            session_id = session_data[0].get('session_id', 'session') if session_data else 'session'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"session_{session_id}_{timestamp}.csv"
        else:
            output_path = Path(output_path)
        
        if not session_data:
            logger.warning("No session data to export")
            return str(output_path)
        
        # Get all fieldnames from first swing
        all_fields = set()
        for swing in session_data:
            all_fields.update(swing.keys())
            all_fields.update(f'metric_{k}' for k in swing.get('metrics', {}).keys())
            all_fields.update(f'shot_{k}' for k in swing.get('shot_data', {}).keys())
        
        # Flatten all swings
        rows = []
        for swing in session_data:
            flat_data = {
                'swing_id': swing.get('swing_id', ''),
                'timestamp': swing.get('timestamp', ''),
                'session_id': swing.get('session_id', ''),
            }
            
            # Add metrics
            metrics = swing.get('metrics', {})
            for key, value in metrics.items():
                flat_data[f'metric_{key}'] = value
            
            # Add flaw analysis
            flaw_analysis = swing.get('flaw_analysis', {})
            flat_data['overall_score'] = flaw_analysis.get('overall_score', 0)
            flat_data['flaw_count'] = flaw_analysis.get('flaw_count', 0)
            
            # Add pro match
            pro_match = swing.get('pro_match', {})
            flat_data['pro_name'] = pro_match.get('golfer_name', '')
            flat_data['similarity_score'] = pro_match.get('similarity_score', 0)
            
            # Add shot data
            shot_data = swing.get('shot_data', {})
            for key, value in shot_data.items():
                flat_data[f'shot_{key}'] = value
            
            rows.append(flat_data)
        
        # Write CSV
        with open(output_path, 'w', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
                writer.writeheader()
                writer.writerows(rows)
        
        logger.info(f"Exported {len(session_data)} swings to CSV: {output_path}")
        return str(output_path)
    
    def export_swing_html(self, swing_data: Dict, output_path: Optional[str] = None) -> str:
        """
        Export swing data to HTML report
        
        Args:
            swing_data: Swing data dictionary
            output_path: Optional output file path
            
        Returns:
            Path to exported HTML file
        """
        if not output_path:
            swing_id = swing_data.get('swing_id', 'swing')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"{swing_id}_{timestamp}.html"
        else:
            output_path = Path(output_path)
        
        # Generate HTML
        html_content = self._generate_swing_html(swing_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Exported swing to HTML: {output_path}")
        return str(output_path)
    
    def export_performance_csv(self, performance_data: List[Dict], output_path: Optional[str] = None) -> str:
        """
        Export performance metrics to CSV
        
        Args:
            performance_data: List of performance metric dictionaries
            output_path: Optional output file path
            
        Returns:
            Path to exported CSV file
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"performance_{timestamp}.csv"
        else:
            output_path = Path(output_path)
        
        if not performance_data:
            logger.warning("No performance data to export")
            return str(output_path)
        
        # Write CSV
        with open(output_path, 'w', newline='') as f:
            if performance_data:
                writer = csv.DictWriter(f, fieldnames=performance_data[0].keys())
                writer.writeheader()
                writer.writerows(performance_data)
        
        logger.info(f"Exported {len(performance_data)} performance records to CSV: {output_path}")
        return str(output_path)
    
    def _generate_swing_html(self, swing_data: Dict) -> str:
        """Generate HTML report for swing"""
        swing_id = swing_data.get('swing_id', 'Unknown')
        timestamp = swing_data.get('timestamp', datetime.now().isoformat())
        metrics = swing_data.get('metrics', {})
        flaw_analysis = swing_data.get('flaw_analysis', {})
        pro_match = swing_data.get('pro_match', {})
        shot_data = swing_data.get('shot_data', {})
        
        # Format metrics table
        metrics_html = ""
        for key, value in metrics.items():
            display_name = key.replace('_', ' ').title()
            metrics_html += f"<tr><td>{display_name}</td><td>{value:.2f}</td></tr>"
        
        # Format flaws
        flaws_html = ""
        flaws = flaw_analysis.get('flaws', [])
        for flaw in flaws[:5]:  # Top 5 flaws
            severity = flaw.get('severity', 0)
            severity_class = 'bad' if severity > 0.7 else 'warning' if severity > 0.4 else 'good'
            flaws_html += f"""
            <div class="flaw-item {severity_class}">
                <strong>{flaw.get('metric', '').replace('_', ' ').title()}</strong>
                <p>{flaw.get('issue', '')}</p>
                <p class="recommendation">{flaw.get('recommendation', '')}</p>
            </div>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ProMirrorGolf - Swing Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #141414;
            padding: 40px;
            border-radius: 8px;
        }}
        h1 {{
            color: #ff4444;
            margin-top: 0;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            background: #1a1a1a;
            border-radius: 4px;
        }}
        .section h2 {{
            color: #ff4444;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #2a2a2a;
        }}
        th {{
            color: #888;
            font-weight: bold;
        }}
        .flaw-item {{
            margin: 15px 0;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid;
        }}
        .flaw-item.bad {{
            background: #2a1a1a;
            border-color: #f44336;
        }}
        .flaw-item.warning {{
            background: #2a241a;
            border-color: #ff9800;
        }}
        .flaw-item.good {{
            background: #1a2a1a;
            border-color: #4caf50;
        }}
        .recommendation {{
            color: #888;
            font-style: italic;
            margin-top: 8px;
        }}
        .score {{
            font-size: 2em;
            color: #4caf50;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ProMirrorGolf Swing Analysis Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Swing ID: {swing_id}</p>
        <p>Timestamp: {timestamp}</p>
        
        <div class="section">
            <h2>Overall Score</h2>
            <div class="score">{flaw_analysis.get('overall_score', 0):.1f}/100</div>
        </div>
        
        <div class="section">
            <h2>Metrics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                {metrics_html}
            </table>
        </div>
        
        <div class="section">
            <h2>Pro Match</h2>
            <p><strong>Golfer:</strong> {pro_match.get('golfer_name', 'N/A')}</p>
            <p><strong>Similarity:</strong> {pro_match.get('similarity_score', 0):.1f}%</p>
        </div>
        
        <div class="section">
            <h2>Key Flaws & Recommendations</h2>
            {flaws_html if flaws_html else '<p>No significant flaws detected.</p>'}
        </div>
        
        {f'''
        <div class="section">
            <h2>Shot Data</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                {''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in shot_data.items())}
            </table>
        </div>
        ''' if shot_data else ''}
        
        <div class="section">
            <p style="color: #888; font-size: 0.9em;">
                Report generated by ProMirrorGolf AI Swing Analysis System
            </p>
        </div>
    </div>
</body>
</html>
        """
        return html
    
    def export_session_summary_pdf(self, session_data: List[Dict], output_path: Optional[str] = None) -> str:
        """
        Export session summary to PDF (requires reportlab)
        
        Args:
            session_data: List of swing data dictionaries
            output_path: Optional output file path
            
        Returns:
            Path to exported PDF file
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            logger.warning("reportlab not available, PDF export disabled")
            # Fallback to HTML
            return self.export_session_summary_html(session_data, output_path)
        
        if not output_path:
            session_id = session_data[0].get('session_id', 'session') if session_data else 'session'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"session_{session_id}_{timestamp}.pdf"
        else:
            output_path = Path(output_path)
        
        # Create PDF
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph("ProMirrorGolf Session Summary", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary stats
        total_swings = len(session_data)
        avg_scores = [s.get('flaw_analysis', {}).get('overall_score', 0) for s in session_data]
        avg_score = sum(avg_scores) / len(avg_scores) if avg_scores else 0
        
        story.append(Paragraph(f"Total Swings: {total_swings}", styles['Normal']))
        story.append(Paragraph(f"Average Score: {avg_score:.1f}/100", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Swings table
        data = [['Swing ID', 'Score', 'Pro Match', 'Similarity']]
        for swing in session_data:
            pro_match = swing.get('pro_match', {})
            data.append([
                swing.get('swing_id', '')[:8],
                f"{swing.get('flaw_analysis', {}).get('overall_score', 0):.1f}",
                pro_match.get('golfer_name', 'N/A'),
                f"{pro_match.get('similarity_score', 0):.1f}%"
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Exported session summary to PDF: {output_path}")
        return str(output_path)
    
    def export_session_summary_html(self, session_data: List[Dict], output_path: Optional[str] = None) -> str:
        """
        Export session summary to HTML
        
        Args:
            session_data: List of swing data dictionaries
            output_path: Optional output file path
            
        Returns:
            Path to exported HTML file
        """
        if not output_path:
            session_id = session_data[0].get('session_id', 'session') if session_data else 'session'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"session_summary_{session_id}_{timestamp}.html"
        else:
            output_path = Path(output_path)
        
        # Calculate summary
        total_swings = len(session_data)
        avg_scores = [s.get('flaw_analysis', {}).get('overall_score', 0) for s in session_data]
        avg_score = sum(avg_scores) / len(avg_scores) if avg_scores else 0
        
        # Generate HTML
        swings_html = ""
        for swing in session_data:
            pro_match = swing.get('pro_match', {})
            swings_html += f"""
            <tr>
                <td>{swing.get('swing_id', '')[:8]}</td>
                <td>{swing.get('flaw_analysis', {}).get('overall_score', 0):.1f}</td>
                <td>{pro_match.get('golfer_name', 'N/A')}</td>
                <td>{pro_match.get('similarity_score', 0):.1f}%</td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ProMirrorGolf - Session Summary</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #141414;
            padding: 40px;
            border-radius: 8px;
        }}
        h1 {{
            color: #ff4444;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: #1a1a1a;
            padding: 20px;
            border-radius: 4px;
        }}
        .stat-value {{
            font-size: 2em;
            color: #4caf50;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #2a2a2a;
        }}
        th {{
            color: #888;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ProMirrorGolf Session Summary</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="stat-card">
                <div>Total Swings</div>
                <div class="stat-value">{total_swings}</div>
            </div>
            <div class="stat-card">
                <div>Average Score</div>
                <div class="stat-value">{avg_score:.1f}</div>
            </div>
        </div>
        
        <h2>Swing Details</h2>
        <table>
            <tr>
                <th>Swing ID</th>
                <th>Score</th>
                <th>Pro Match</th>
                <th>Similarity</th>
            </tr>
            {swings_html}
        </table>
    </div>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Exported session summary to HTML: {output_path}")
        return str(output_path)

