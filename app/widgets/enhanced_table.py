"""Enhanced table widget with Excel-style header filtering and sorting."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Callable

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
from PyQt6.QtWidgets import (
    QHeaderView,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QComboBox,
)

logger = logging.getLogger(__name__)


class FilterableTableWidget(QWidget):
    """Enhanced table widget with Excel-style header filtering and sorting."""
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        columns: Optional[list[str]] = None,
        filterable_columns: Optional[list[int]] = None,
        table_id: Optional[str] = None,
    ) -> None:
        super().__init__(parent)
        self.columns = columns or []
        self.filterable_columns = filterable_columns or list(range(len(self.columns)))
        self.column_filters = {}  # column_index -> filter_text
        self.table_id = table_id or f"table_{id(self)}"
        
        # Load column preferences
        from core.column_preferences import ColumnPreferencesManager
        prefs_file = Path("data") / "column_preferences.json"
        self.prefs_manager = ColumnPreferencesManager(prefs_file)
        
        self._setup_ui()
        self._load_column_preferences()
    
    def _setup_ui(self) -> None:
        """Set up the UI with table and header filtering."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Table widget
        self.table = QTableWidget(0, len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(True)
        
        # Enable scroll wheel with smooth scrolling
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        # Enable scrollbars
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set size policy to expand properly
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Make headers visible, clickable, and add filter menu
        header = self.table.horizontalHeader()
        header.setVisible(True)
        header.setSectionsClickable(True)
        header.setSectionsMovable(False)
        header.setStretchLastSection(False)
        header.setDefaultSectionSize(120)
        header.setMinimumHeight(40)  # Ensure header has enough height to be visible
        
        # Enable column reordering
        header.setSectionsMovable(True)
        
        # Connect header context menu for filtering and customization
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_menu)
        
        # Style the table
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_MEDIUM}px;
                gridline-color: transparent;
                color: {current_colors.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
                border: none;
                border-bottom: 1px solid {current_colors.BORDER_DEFAULT};
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.BODY}px;
            }}
            QTableWidget::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QTableWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
            }}
            QHeaderView::section {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                color: {current_colors.TEXT_SECONDARY};
                padding: {SPACING.MEDIUM}px {SPACING.MEDIUM}px;
                border: none;
                border-bottom: 2px solid {current_colors.BORDER_DEFAULT};
                border-right: 1px solid {current_colors.BORDER_DEFAULT};
                font-size: {TYPOGRAPHY.TINY}px;
                font-weight: {TYPOGRAPHY.BOLD};
            }}
            QHeaderView::section:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                color: {current_colors.TEXT_PRIMARY};
            }}
            QHeaderView::section:pressed {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        
        layout.addWidget(self.table, 1)
        
        # Pagination controls (initially hidden)
        self.pagination_widget = QWidget()
        pagination_layout = QHBoxLayout(self.pagination_widget)
        pagination_layout.setContentsMargins(SPACING.SMALL, SPACING.XS, SPACING.SMALL, SPACING.XS)
        pagination_layout.setSpacing(SPACING.SMALL)
        
        self.prev_page_btn = QPushButton("◀")
        self.prev_page_btn.setToolTip("Previous page")
        self.prev_page_btn.setEnabled(False)
        self.prev_page_btn.setFixedSize(32, 24)
        self.prev_page_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                color: {current_colors.TEXT_PRIMARY};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover:enabled {{
                background-color: {current_colors.BORDER_HOVER};
            }}
            QPushButton:disabled {{
                color: {current_colors.TEXT_DISABLED};
            }}
        """)
        pagination_layout.addWidget(self.prev_page_btn)
        
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setAutoFillBackground(True)
        self.page_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: 0 {SPACING.SMALL}px; margin: 0px;")
        pagination_layout.addWidget(self.page_label)
        
        self.next_page_btn = QPushButton("▶")
        self.next_page_btn.setToolTip("Next page")
        self.next_page_btn.setEnabled(False)
        self.next_page_btn.setFixedSize(32, 24)
        self.next_page_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
                color: {current_colors.TEXT_PRIMARY};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QPushButton:hover:enabled {{
                background-color: {current_colors.BORDER_HOVER};
            }}
            QPushButton:disabled {{
                color: {current_colors.TEXT_DISABLED};
            }}
        """)
        pagination_layout.addWidget(self.next_page_btn)
        
        pagination_layout.addStretch()
        
        self.rows_per_page_combo = QComboBox()
        self.rows_per_page_combo.addItems(["25", "50", "100", "250", "500", "All"])
        self.rows_per_page_combo.setCurrentText("100")
        self.rows_per_page_combo.setFixedWidth(80)
        self.rows_per_page_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px {SPACING.SMALL}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QComboBox:hover {{
                border-color: {current_colors.BORDER_ACTIVE};
            }}
        """)
        pagination_layout.addWidget(QLabel("Rows:"))
        pagination_layout.addWidget(self.rows_per_page_combo)
        
        self.pagination_widget.hide()
        layout.addWidget(self.pagination_widget)
        
        # Pagination state
        self.pagination_enabled = False
        self.current_page = 1
        self.rows_per_page = 100
        self.total_rows = 0
        self.data_loader: Optional[Callable] = None  # Function to load data for a page
        
        # Connect pagination signals
        self.prev_page_btn.clicked.connect(self._prev_page)
        self.next_page_btn.clicked.connect(self._next_page)
        self.rows_per_page_combo.currentTextChanged.connect(self._on_rows_per_page_changed)
        
        # Row count label (small, at bottom)
        self.row_count_label = QLabel("0 rows")
        self.row_count_label.setAutoFillBackground(True)
        self.row_count_label.setStyleSheet(f"background-color: {current_colors.BACKGROUND_BASE}; color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: {SPACING.XS}px {SPACING.SMALL}px; margin: 0px;")
        layout.addWidget(self.row_count_label)
    
    def _show_header_menu(self, position: QPoint) -> None:
        """Show context menu for header with filter and sort options."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        column = self.table.horizontalHeader().logicalIndexAt(position)
        if column < 0 or column >= len(self.columns):
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px;
            }}
            QMenu::item {{
                padding: {SPACING.SMALL}px {SPACING.LARGE}px {SPACING.SMALL}px {SPACING.MEDIUM}px;
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QMenu::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {current_colors.BORDER_HOVER};
                margin: {SPACING.XS}px {SPACING.SMALL}px;
            }}
        """)
        
        # Sort options
        sort_asc = QAction("Sort A → Z", self)
        sort_asc.triggered.connect(lambda: self._sort_column(column, Qt.SortOrder.AscendingOrder))
        menu.addAction(sort_asc)
        
        sort_desc = QAction("Sort Z → A", self)
        sort_desc.triggered.connect(lambda: self._sort_column(column, Qt.SortOrder.DescendingOrder))
        menu.addAction(sort_desc)
        
        menu.addSeparator()
        
        # Column customization
        customize_action = QAction("Customize Columns...", self)
        customize_action.triggered.connect(self._show_column_customization_dialog)
        menu.addAction(customize_action)
        
        menu.addSeparator()
        
        # Filter option (only for filterable columns)
        if column in self.filterable_columns:
            filter_action = QAction("Filter...", self)
            filter_action.triggered.connect(lambda: self._show_filter_dialog(column))
            menu.addAction(filter_action)
            
            # Clear filter if exists
            if column in self.column_filters and self.column_filters[column]:
                clear_filter = QAction("Clear Filter", self)
                clear_filter.triggered.connect(lambda: self._clear_column_filter(column))
                menu.addAction(clear_filter)
        
        menu.exec(self.table.horizontalHeader().mapToGlobal(position))
    
    def _sort_column(self, column: int, order: Qt.SortOrder) -> None:
        """Sort table by column."""
        self.table.sortItems(column, order)
    
    def _show_filter_dialog(self, column: int) -> None:
        """Show filter dialog for a column."""
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Filter: {self.columns[column]}")
        dialog.setMinimumSize(400, 200)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {current_colors.BACKGROUND_CONTROL};
            }}
            QLabel {{
                color: {current_colors.TEXT_PRIMARY};
                font-size: {TYPOGRAPHY.TINY}px;
            }}
            QLineEdit {{
                background-color: {current_colors.BACKGROUND_SURFACE};
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
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        label = QLabel(f"Filter {self.columns[column]} by text:")
        layout.addWidget(label)
        
        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Enter text to filter...")
        if column in self.column_filters:
            filter_input.setText(self.column_filters[column])
        layout.addWidget(filter_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            filter_text = filter_input.text().strip()
            if filter_text:
                self.column_filters[column] = filter_text
            else:
                self.column_filters.pop(column, None)
            self._apply_filters()
    
    def _clear_column_filter(self, column: int) -> None:
        """Clear filter for a column."""
        self.column_filters.pop(column, None)
        self._apply_filters()
    
    def _apply_filters(self) -> None:
        """Apply all column filters."""
        if not self.column_filters:
            # Show all rows
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
        else:
            # Apply filters
            for row in range(self.table.rowCount()):
                show_row = True
                for col, filter_text in self.column_filters.items():
                    if col >= self.table.columnCount():
                        continue
                    item = self.table.item(row, col)
                    if item and filter_text.lower() not in item.text().lower():
                        show_row = False
                        break
                self.table.setRowHidden(row, not show_row)
        
        self._update_row_count()
    
    def _update_row_count(self) -> None:
        """Update the row count label."""
        visible_rows = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
        total_rows = self.table.rowCount()
        if visible_rows == total_rows:
            self.row_count_label.setText(f"{total_rows} row{'s' if total_rows != 1 else ''}")
        else:
            self.row_count_label.setText(f"{visible_rows} of {total_rows} row{'s' if total_rows != 1 else ''}")
    
    def add_row(self, items: list[str | QTableWidgetItem], data: Optional[dict] = None) -> int:
        """Add a row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        for col, item in enumerate(items):
            if isinstance(item, str):
                table_item = QTableWidgetItem(item)
            else:
                table_item = item
            
            table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, col, table_item)
        
        if data:
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole + 1, data)
        
        self._update_row_count()
        return row
    
    def clear(self) -> None:
        """Clear all rows."""
        self.table.setRowCount(0)
        self.column_filters.clear()
        self._update_row_count()
    
    def set_column_widths(self, widths: list[int]) -> None:
        """Set column widths."""
        for col, width in enumerate(widths):
            if col < self.table.columnCount():
                self.table.setColumnWidth(col, width)
    
    def set_column_stretch(self, column: int, stretch: bool = True) -> None:
        """Set whether a column should stretch."""
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch if stretch else QHeaderView.ResizeMode.Interactive)
    
    def _load_column_preferences(self) -> None:
        """Load and apply column preferences."""
        prefs = self.prefs_manager.get_preferences(self.table_id)
        
        if prefs.get("visible_columns") is not None:
            visible = prefs["visible_columns"]
            for col in range(self.table.columnCount()):
                self.table.setColumnHidden(col, col not in visible)
        
        if prefs.get("column_order") is not None:
            order = prefs["column_order"]
            header = self.table.horizontalHeader()
            # Apply column order by moving sections
            for visual_index, logical_index in enumerate(order):
                if logical_index < self.table.columnCount():
                    current_visual = header.visualIndex(logical_index)
                    if current_visual != visual_index:
                        header.moveSection(current_visual, visual_index)
    
    def _show_column_customization_dialog(self) -> None:
        """Show dialog to customize column visibility and order."""
        from app.design_constants import SPACING
        from app.theme import get_current_theme
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Customize Columns")
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet(get_current_theme())
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(SPACING.LARGE, SPACING.LARGE, SPACING.LARGE, SPACING.LARGE)
        layout.setSpacing(SPACING.MEDIUM)
        
        # Instructions
        from app.design_constants import get_current_colors, SIZES, SPACING, TYPOGRAPHY
        current_colors = get_current_colors()
        
        instructions = QLabel("Check columns to show, uncheck to hide. Drag to reorder.")
        instructions.setStyleSheet(f"color: {current_colors.TEXT_SECONDARY}; font-size: {TYPOGRAPHY.TINY}px; padding: {SPACING.SMALL}px;")
        layout.addWidget(instructions)
        
        # Column list (checkable and reorderable)
        column_list = QListWidget()
        column_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        column_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {current_colors.BACKGROUND_CONTROL};
                border: 1px solid {current_colors.BORDER_HOVER};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.XS}px;
            }}
            QListWidget::item {{
                background-color: {current_colors.BACKGROUND_SURFACE};
                border: 1px solid {current_colors.BORDER_DEFAULT};
                border-radius: {SIZES.BORDER_RADIUS_SMALL}px;
                padding: {SPACING.SMALL}px;
                margin: 2px;
                color: {current_colors.TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
            QListWidget::item:hover {{
                background-color: {current_colors.BACKGROUND_SURFACE_ELEVATED};
            }}
        """)
        
        # Add columns with checkboxes
        header = self.table.horizontalHeader()
        for col in range(self.table.columnCount()):
            item = QListWidgetItem(self.columns[col] if col < len(self.columns) else f"Column {col}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if not self.table.isColumnHidden(col) else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, col)  # Store original column index
            column_list.addItem(item)
        
        layout.addWidget(column_list)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        def restore_defaults() -> None:
            """Restore all columns to visible and default order."""
            column_list.clear()
            for col in range(self.table.columnCount()):
                item = QListWidgetItem(self.columns[col] if col < len(self.columns) else f"Column {col}")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, col)
                column_list.addItem(item)
        
        restore_btn = buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults)
        restore_btn.setText("Restore Defaults")
        restore_btn.clicked.connect(restore_defaults)
        
        layout.addWidget(buttons)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Get visible columns and new order
            visible_columns = []
            column_order = []
            
            for row in range(column_list.count()):
                item = column_list.item(row)
                original_col = item.data(Qt.ItemDataRole.UserRole)
                if item.checkState() == Qt.CheckState.Checked:
                    visible_columns.append(original_col)
                    column_order.append(original_col)
            
            # Apply visibility
            for col in range(self.table.columnCount()):
                self.table.setColumnHidden(col, col not in visible_columns)
            
            # Apply order
            header = self.table.horizontalHeader()
            for visual_index, logical_index in enumerate(column_order):
                current_visual = header.visualIndex(logical_index)
                if current_visual != visual_index:
                    header.moveSection(current_visual, visual_index)
            
            # Save preferences
            self.prefs_manager.save_preferences(
                self.table_id,
                visible_columns if len(visible_columns) < self.table.columnCount() else None,
                column_order if column_order != list(range(self.table.columnCount())) else None
            )
    
    def enable_pagination(self, total_rows: int, data_loader: Callable[[int, int], list]) -> None:
        """
        Enable pagination for the table.
        
        Args:
            total_rows: Total number of rows in the dataset
            data_loader: Function that takes (page, rows_per_page) and returns list of row data
        """
        self.pagination_enabled = True
        self.total_rows = total_rows
        self.data_loader = data_loader
        self.pagination_widget.show()
        self._load_page(1)
    
    def disable_pagination(self) -> None:
        """Disable pagination and show all rows."""
        self.pagination_enabled = False
        self.pagination_widget.hide()
        self.current_page = 1
        self.total_rows = 0
        self.data_loader = None
    
    def _load_page(self, page: int) -> None:
        """Load a specific page of data."""
        if not self.pagination_enabled or not self.data_loader:
            return
        
        rows_per_page = self.rows_per_page if self.rows_per_page > 0 else self.total_rows
        
        if rows_per_page <= 0:
            # "All" selected - load everything
            rows_per_page = self.total_rows
        
        total_pages = max(1, (self.total_rows + rows_per_page - 1) // rows_per_page) if rows_per_page > 0 else 1
        page = max(1, min(page, total_pages))
        
        self.current_page = page
        
        # Load data for this page
        offset = (page - 1) * rows_per_page
        page_data = self.data_loader(offset, rows_per_page)
        
        # Clear and populate table
        self.clear()
        for row_data in page_data:
            if isinstance(row_data, list):
                self.add_row(row_data)
            elif isinstance(row_data, dict):
                # Assume dict has 'items' key for row items
                self.add_row(row_data.get('items', []), row_data.get('data'))
        
        # Update pagination controls
        self._update_pagination_controls(total_pages)
    
    def _update_pagination_controls(self, total_pages: int) -> None:
        """Update pagination control states."""
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)
        self.page_label.setText(f"Page {self.current_page} of {total_pages}")
        
        # Update row count label
        rows_per_page = self.rows_per_page if self.rows_per_page > 0 else self.total_rows
        start_row = (self.current_page - 1) * rows_per_page + 1
        end_row = min(self.current_page * rows_per_page, self.total_rows)
        self.row_count_label.setText(f"Showing {start_row}-{end_row} of {self.total_rows} rows")
    
    def _prev_page(self) -> None:
        """Go to previous page."""
        if self.current_page > 1:
            self._load_page(self.current_page - 1)
    
    def _next_page(self) -> None:
        """Go to next page."""
        rows_per_page = self.rows_per_page if self.rows_per_page > 0 else self.total_rows
        total_pages = max(1, (self.total_rows + rows_per_page - 1) // rows_per_page) if rows_per_page > 0 else 1
        if self.current_page < total_pages:
            self._load_page(self.current_page + 1)
    
    def _on_rows_per_page_changed(self, text: str) -> None:
        """Handle rows per page change."""
        if text == "All":
            self.rows_per_page = 0  # 0 means load all
        else:
            try:
                self.rows_per_page = int(text)
            except ValueError:
                self.rows_per_page = 100
        
        # Reload current page (or first page if current page would be invalid)
        self._load_page(1)
