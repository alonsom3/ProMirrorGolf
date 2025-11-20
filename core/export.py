"""Export functionality for sessions and shots."""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def export_session_to_csv(session, shots: list, output_path: Path) -> bool:
    """Export a session and its shots to CSV."""
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Session header
            writer.writerow(["Session Information"])
            writer.writerow(["Name", session.name])
            writer.writerow(["Club", session.club or ""])
            writer.writerow(["Notes", session.notes or ""])
            writer.writerow(["Started", session.started_at.strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["Ended", session.ended_at.strftime("%Y-%m-%d %H:%M:%S") if session.ended_at else ""])
            writer.writerow([])
            
            # Shots header
            writer.writerow(["Shots"])
            headers = [
                "Time", "Club Speed", "Ball Speed", "Launch Angle", "Spin Rate",
                "Carry Distance", "Total Distance", "Side Spin", "Back Spin",
                "Launch Direction", "Apex Height", "Descent Angle",
                "Smash Factor", "Dynamic Loft", "Attack Angle", "Club Path", "Face Angle",
                "DTL Video", "Face Video", "Notes"
            ]
            writer.writerow(headers)
            
            # Shot data
            for shot in shots:
                row = [
                    shot.recorded_at.strftime("%H:%M:%S"),
                    shot.club_speed or "",
                    shot.ball_speed or "",
                    shot.launch_angle or "",
                    shot.spin_rate or "",
                    shot.carry_distance or "",
                    shot.total_distance or "",
                    shot.side_spin or "",
                    shot.back_spin or "",
                    shot.launch_direction or "",
                    shot.apex_height or "",
                    shot.descent_angle or "",
                    shot.smash_factor or "",
                    shot.dynamic_loft or "",
                    shot.attack_angle or "",
                    shot.club_path or "",
                    shot.face_angle or "",
                    shot.dtl_video_path or "",
                    shot.face_video_path or "",
                    shot.notes or "",
                ]
                writer.writerow(row)
        
        logger.info("Exported session %d to CSV: %s", session.id, output_path)
        return True
    except Exception as e:
        logger.error("Error exporting to CSV: %s", e, exc_info=True)
        return False


def export_session_to_json(session, shots: list, output_path: Path) -> bool:
    """Export a session and its shots to JSON."""
    try:
        data = {
            "session": {
                "id": session.id,
                "name": session.name,
                "club": session.club,
                "notes": session.notes,
                "started_at": session.started_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "tags": json.loads(session.tags) if session.tags else [],
                "is_favorite": session.is_favorite,
            },
            "shots": []
        }
        
        for shot in shots:
            shot_data = {
                "id": shot.id,
                "recorded_at": shot.recorded_at.isoformat(),
                "club_speed": shot.club_speed,
                "ball_speed": shot.ball_speed,
                "launch_angle": shot.launch_angle,
                "spin_rate": shot.spin_rate,
                "carry_distance": shot.carry_distance,
                "total_distance": shot.total_distance,
                "side_spin": shot.side_spin,
                "back_spin": shot.back_spin,
                "launch_direction": shot.launch_direction,
                "apex_height": shot.apex_height,
                "descent_angle": shot.descent_angle,
                "smash_factor": shot.smash_factor,
                "dynamic_loft": shot.dynamic_loft,
                "attack_angle": shot.attack_angle,
                "club_path": shot.club_path,
                "face_angle": shot.face_angle,
                "dtl_video_path": shot.dtl_video_path,
                "face_video_path": shot.face_video_path,
                "tags": json.loads(shot.tags) if shot.tags else [],
                "is_favorite": shot.is_favorite,
                "notes": shot.notes,
                "raw_json": json.loads(shot.raw_json) if shot.raw_json else {},
            }
            data["shots"].append(shot_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info("Exported session %d to JSON: %s", session.id, output_path)
        return True
    except Exception as e:
        logger.error("Error exporting to JSON: %s", e, exc_info=True)
        return False


def export_session_to_pdf(session, shots: list, output_path: Path) -> bool:
    """Export a session and its shots to PDF report."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#ff4d4d'),
            spaceAfter=30,
        )
        story.append(Paragraph(f"Session Report: {session.name}", title_style))
        
        # Session info
        session_data = [
            ["Session Information", ""],
            ["Name:", session.name],
            ["Club:", session.club or "N/A"],
            ["Started:", session.started_at.strftime("%Y-%m-%d %H:%M:%S")],
            ["Ended:", session.ended_at.strftime("%Y-%m-%d %H:%M:%S") if session.ended_at else "N/A"],
        ]
        if session.notes:
            session_data.append(["Notes:", session.notes])
        
        session_table = Table(session_data, colWidths=[2*inch, 4*inch])
        session_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a2a2a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(session_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Shots summary
        if shots:
            story.append(Paragraph(f"Shots Summary ({len(shots)} total)", styles['Heading2']))
            
            # Summary stats
            club_speeds = [s.club_speed for s in shots if s.club_speed]
            ball_speeds = [s.ball_speed for s in shots if s.ball_speed]
            distances = [s.carry_distance for s in shots if s.carry_distance]
            
            summary_data = [
                ["Metric", "Average", "Min", "Max"],
                ["Club Speed (mph)", f"{sum(club_speeds)/len(club_speeds):.1f}" if club_speeds else "N/A", f"{min(club_speeds):.1f}" if club_speeds else "N/A", f"{max(club_speeds):.1f}" if club_speeds else "N/A"],
                ["Ball Speed (mph)", f"{sum(ball_speeds)/len(ball_speeds):.1f}" if ball_speeds else "N/A", f"{min(ball_speeds):.1f}" if ball_speeds else "N/A", f"{max(ball_speeds):.1f}" if ball_speeds else "N/A"],
                ["Carry Distance (yds)", f"{sum(distances)/len(distances):.1f}" if distances else "N/A", f"{min(distances):.1f}" if distances else "N/A", f"{max(distances):.1f}" if distances else "N/A"],
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a2a2a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Detailed shots table (first 20 shots)
            story.append(Paragraph("Shot Details", styles['Heading2']))
            shot_headers = ["Time", "Club Speed", "Ball Speed", "Spin", "Carry", "Total"]
            shot_data = [shot_headers]
            
            for shot in shots[:20]:  # Limit to first 20 for PDF
                shot_data.append([
                    shot.recorded_at.strftime("%H:%M:%S"),
                    f"{shot.club_speed:.1f}" if shot.club_speed else "N/A",
                    f"{shot.ball_speed:.1f}" if shot.ball_speed else "N/A",
                    f"{shot.spin_rate:.0f}" if shot.spin_rate else "N/A",
                    f"{shot.carry_distance:.1f}" if shot.carry_distance else "N/A",
                    f"{shot.total_distance:.1f}" if shot.total_distance else "N/A",
                ])
            
            if len(shots) > 20:
                shot_data.append([f"... and {len(shots) - 20} more shots", "", "", "", "", ""])
            
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
        
        doc.build(story)
        logger.info("Exported session %d to PDF: %s", session.id, output_path)
        return True
    except ImportError:
        logger.error("reportlab not installed. Install with: pip install reportlab")
        return False
    except Exception as e:
        logger.error("Error exporting to PDF: %s", e, exc_info=True)
        return False


# Wrapper functions for backward compatibility with tests
def export_session_to_csv_by_id(session_id: int, output_path: str, engine) -> bool:
    """Export session to CSV by session ID (wrapper for tests)."""
    from sqlalchemy.orm import Session
    from core.session_manager import SessionModel
    
    with Session(engine) as session:
        sess = session.get(SessionModel, session_id)
        if not sess:
            return False
        shots = list(sess.shots) if sess.shots else []
        return export_session_to_csv(sess, shots, Path(output_path))


def export_session_to_json_by_id(session_id: int, output_path: str, engine) -> bool:
    """Export session to JSON by session ID (wrapper for tests)."""
    from sqlalchemy.orm import Session
    from core.session_manager import SessionModel
    
    with Session(engine) as session:
        sess = session.get(SessionModel, session_id)
        if not sess:
            return False
        shots = list(sess.shots) if sess.shots else []
        return export_session_to_json(sess, shots, Path(output_path))


def export_session_to_pdf_by_id(session_id: int, output_path: str, engine) -> bool:
    """Export session to PDF by session ID (wrapper for tests)."""
    from sqlalchemy.orm import Session
    from core.session_manager import SessionModel
    
    with Session(engine) as session:
        sess = session.get(SessionModel, session_id)
        if not sess:
            return False
        shots = list(sess.shots) if sess.shots else []
        return export_session_to_pdf(sess, shots, Path(output_path))
