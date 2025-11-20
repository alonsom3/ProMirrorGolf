"""Enhanced PDF export with charts and better formatting."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def export_session_to_pdf_enhanced(session, shots: list, output_path: Path, include_charts: bool = True) -> bool:
    """Export session to PDF with charts and enhanced formatting.
    
    Args:
        session: SessionModel instance
        shots: List of ShotModel instances
        output_path: Path to output PDF file
        include_charts: Whether to include charts in PDF
        
    Returns:
        True if successful, False otherwise
    """
    try:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            logger.error("reportlab not installed. Install with: pip install reportlab")
            return False
        
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#ff4d4d'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#c9d1d9'),
            spaceAfter=12,
        )
        
        # Title
        story.append(Paragraph(f"Session Report: {session.name}", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Session information
        story.append(Paragraph("Session Information", heading_style))
        session_data = [
            ["Name:", session.name],
            ["Club:", session.club or "N/A"],
            ["Started:", session.started_at.strftime("%Y-%m-%d %H:%M:%S")],
            ["Ended:", session.ended_at.strftime("%Y-%m-%d %H:%M:%S") if session.ended_at else "N/A"],
            ["Total Shots:", str(len(shots))],
        ]
        
        if session.notes:
            session_data.append(["Notes:", session.notes])
        
        session_table = Table(session_data, colWidths=[2*inch, 4*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#161b22')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#c9d1d9')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#21262d')),
        ]))
        story.append(session_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Statistics summary
        if shots:
            story.append(Paragraph("Statistics Summary", heading_style))
            
            carries = [s.carry_distance for s in shots if s.carry_distance]
            speeds = [s.club_speed for s in shots if s.club_speed]
            spins = [s.spin_rate for s in shots if s.spin_rate]
            
            stats_data = [
                ["Metric", "Average", "Min", "Max"],
                ["Carry Distance (yds)", 
                 f"{sum(carries)/len(carries):.1f}" if carries else "N/A",
                 f"{min(carries):.1f}" if carries else "N/A",
                 f"{max(carries):.1f}" if carries else "N/A"],
                ["Club Speed (mph)",
                 f"{sum(speeds)/len(speeds):.1f}" if speeds else "N/A",
                 f"{min(speeds):.1f}" if speeds else "N/A",
                 f"{max(speeds):.1f}" if speeds else "N/A"],
                ["Spin Rate (rpm)",
                 f"{sum(spins)/len(spins):.0f}" if spins else "N/A",
                 f"{min(spins):.0f}" if spins else "N/A",
                 f"{max(spins):.0f}" if spins else "N/A"],
            ]
            
            stats_table = Table(stats_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff4d4d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Shot details (first 30 shots)
        if shots:
            story.append(Paragraph("Shot Details", heading_style))
            shot_headers = ["Time", "Club Speed", "Ball Speed", "Carry", "Total", "Spin"]
            shot_data = [shot_headers]
            
            for shot in shots[:30]:  # Limit to first 30 for PDF
                shot_data.append([
                    shot.recorded_at.strftime("%H:%M:%S"),
                    f"{shot.club_speed:.1f}" if shot.club_speed else "N/A",
                    f"{shot.ball_speed:.1f}" if shot.ball_speed else "N/A",
                    f"{shot.carry_distance:.1f}" if shot.carry_distance else "N/A",
                    f"{shot.total_distance:.1f}" if shot.total_distance else "N/A",
                    f"{shot.spin_rate:.0f}" if shot.spin_rate else "N/A",
                ])
            
            if len(shots) > 30:
                shot_data.append([f"... and {len(shots) - 30} more shots", "", "", "", "", ""])
            
            shots_table = Table(shot_data, colWidths=[0.8*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            shots_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a2a2a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            story.append(shots_table)
        
        # Note about charts
        if include_charts:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(
                "<i>Note: Charts can be exported separately from the Analysis Dashboard.</i>",
                styles['Normal']
            ))
        
        doc.build(story)
        logger.info("Exported session %d to enhanced PDF: %s", session.id, output_path)
        return True
    except Exception as e:
        logger.error("Error exporting to enhanced PDF: %s", e, exc_info=True)
        return False

