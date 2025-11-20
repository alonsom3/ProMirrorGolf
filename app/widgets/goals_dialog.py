"""Goals management dialog."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
)

from app.design_constants import SPACING, SIZES, TYPOGRAPHY
from app.theme import get_current_theme
from core.goals import GoalModel, add_goal, check_goal_progress, create_goal_table, get_goals

logger = logging.getLogger(__name__)


class GoalsDialog(QDialog):
    """Dialog for managing goals."""
    
    def __init__(self, session_manager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.session_manager = session_manager
        self.setWindowTitle("Goals Management")
        self.setMinimumSize(700, 500)  # More flexible for smaller screens
        self.resize(900, 650)  # Smaller default size
        self.setSizeGripEnabled(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setStyleSheet(get_current_theme())
        
        # Create goals table if needed
        create_goal_table(self.session_manager.engine)
        
        self._build_ui()
        self._load_goals()
    
    def _build_ui(self) -> None:
        """Build UI."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING.MEDIUM)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Goals")
        title.setAutoFillBackground(True)
        title.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.H3}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("Add Goal")
        add_btn.setMinimumHeight(32)
        add_btn.setMaximumHeight(40)
        add_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.ACCENT};
                border: 1px solid {current_colors.ACCENT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 6px {SPACING.MEDIUM}px;
                color: {current_colors.WHITE_TEXT};
                font-weight: {TYPOGRAPHY.BOLD};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.ACCENT_HOVER};
            }}
        """)
        add_btn.clicked.connect(self._add_goal)
        header_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setMinimumHeight(32)
        refresh_btn.setMaximumHeight(40)
        refresh_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: 6px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        refresh_btn.clicked.connect(self._load_goals)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header)
        
        # Goals table with enhanced features
        from app.widgets.enhanced_table import FilterableTableWidget
        
        self.goals_table_widget = FilterableTableWidget(
            columns=["Name", "Metric", "Target", "Operator", "Progress", "Status", "Actions"],
            filterable_columns=[0, 1, 4, 5],  # Name, Metric, Progress, Status
            table_id="goals_table",
        )
        self.goals_table = self.goals_table_widget.table
        
        # Enable sorting
        self.goals_table.setSortingEnabled(True)
        
        # Enable scroll wheel
        self.goals_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.goals_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # Make headers visible and clickable
        header = self.goals_table.horizontalHeader()
        header.setVisible(True)
        header.setSectionsClickable(True)
        
        # Set column widths
        self.goals_table_widget.set_column_widths([150, 120, 100, 80, 150, 80, 100])
        
        layout.addWidget(self.goals_table_widget, 1)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover {{
                background-color: {current_colors.BORDER_HOVER};
            }}
        """)
        layout.addWidget(buttons)
    
    def _load_goals(self) -> None:
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()

        """Load and display goals."""
        from sqlalchemy.orm import Session
        from core.session_manager import ShotModel
        
        try:
            with Session(self.session_manager.engine) as db_session:
                goals = get_goals(db_session, active_only=True)
                
                self.goals_table_widget.clear()
                
                for goal in goals:
                    # Get all shots for progress calculation
                    shots_query = db_session.query(ShotModel)
                    if goal.club_type:
                        shots_query = shots_query.join(ShotModel.session).filter(
                            ShotModel.session.has(club=goal.club_type)
                        )
                    shots = shots_query.all()
                    
                    progress = check_goal_progress(db_session, goal, shots)
                    
                    if progress["total_shots"] > 0:
                        progress_text = f"{progress['achieved']}/{progress['total_shots']} ({progress['percentage']:.1f}%)"
                    else:
                        progress_text = "No data"
                    
                    status = "Active" if goal.is_active else "Inactive"
                    
                    row = self.goals_table_widget.add_row([
                        goal.name,
                        goal.metric,
                        f"{goal.target_value}",
                        goal.operator,
                        progress_text,
                        status,
                        "",  # Actions column - will be set below
                    ])
                    
                    # Actions button
                    delete_btn = QPushButton("Delete")
                    delete_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                            border: 1px solid {current_colors.DANGER};
                            border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                            padding: {SPACING.XS}px {SPACING.SMALL}px;
                            color: {current_colors.DANGER_TEXT};
                            font-size: {TYPOGRAPHY.TINY}px;
                        }}
                        QPushButton:hover {{
                            background-color: {current_colors.DANGER_HOVER};
                            color: {current_colors.WHITE_TEXT};
                        }}
                    """)
                    delete_btn.clicked.connect(lambda checked, g=goal: self._delete_goal(g))
                    self.goals_table.setCellWidget(row, 6, delete_btn)
        except Exception as e:
            logger.error("Error loading goals: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load goals: {str(e)}")
    
    def _add_goal(self) -> None:
        """Add a new goal."""
        from app.design_constants import get_current_colors
        current_colors = get_current_colors()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Goal")
        dialog.setMinimumSize(500, 400)
        dialog.resize(600, 450)
        dialog.setStyleSheet(get_current_theme())
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        # Name
        name_label = QLabel("Goal Name:")
        name_label.setAutoFillBackground(True)
        name_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        layout.addWidget(name_label)
        
        name_edit = QLineEdit()
        name_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {current_colors.ACCENT};
            }}
        """)
        layout.addWidget(name_edit)
        
        # Metric
        metric_label = QLabel("Metric:")
        metric_label.setAutoFillBackground(True)
        metric_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_PRIMARY}; font-size: {TYPOGRAPHY.BODY}px; font-weight: {TYPOGRAPHY.BOLD}; padding: 0px; margin: 0px;")
        layout.addWidget(metric_label)
        
        metric_combo = QComboBox()
        metric_combo.addItems([
            "club_speed", "ball_speed", "carry_distance", "total_distance",
            "spin_rate", "launch_angle", "smash_factor"
        ])
        metric_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QComboBox:focus {{
                border: 1px solid {current_colors.ACCENT};
            }}
        """)
        layout.addWidget(metric_combo)
        
        # Target value and operator
        target_layout = QHBoxLayout()
        
        operator_combo = QComboBox()
        operator_combo.addItems([">=", "<=", "=="])
        operator_combo.setStyleSheet(metric_combo.styleSheet())
        target_layout.addWidget(operator_combo)
        
        target_spin = QDoubleSpinBox()
        target_spin.setMinimum(0)
        target_spin.setMaximum(10000)
        target_spin.setStyleSheet(metric_combo.styleSheet())
        target_layout.addWidget(target_spin)
        
        layout.addLayout(target_layout)
        
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            from sqlalchemy.orm import Session
            
            try:
                with Session(self.session_manager.engine) as db_session:
                    add_goal(
                        db_session,
                        name=name_edit.text().strip(),
                        metric=metric_combo.currentText(),
                        target_value=target_spin.value(),
                        operator=operator_combo.currentText(),
                    )
                self._load_goals()
                QMessageBox.information(self, "Success", "Goal added successfully.")
            except Exception as e:
                logger.error("Error adding goal: %s", e, exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to add goal: {str(e)}")
    
    def _delete_goal(self, goal: GoalModel) -> None:
        """Delete a goal."""
        reply = QMessageBox.question(
            self,
            "Delete Goal",
            f"Are you sure you want to delete goal '{goal.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            from sqlalchemy.orm import Session
            
            try:
                with Session(self.session_manager.engine) as db_session:
                    db_session.delete(goal)
                    db_session.commit()
                self._load_goals()
                QMessageBox.information(self, "Success", "Goal deleted successfully.")
            except Exception as e:
                logger.error("Error deleting goal: %s", e, exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to delete goal: {str(e)}")

