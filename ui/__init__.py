"""
ProMirrorGolf UI Modules
Modular UI components for maintainability
"""

from .main_window import MainWindow
from .viewer_panel import ViewerPanel
from .controls_panel import ControlsPanel
from .metrics_panel import MetricsPanel
from .progress_panel import ProgressPanel
from .performance_dashboard import PerformanceDashboard
from .dialogs import Dialogs

__all__ = [
    'MainWindow',
    'ViewerPanel',
    'ControlsPanel',
    'MetricsPanel',
    'ProgressPanel',
    'PerformanceDashboard',
    'Dialogs'
]

