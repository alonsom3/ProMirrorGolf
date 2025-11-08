"""
Metrics Panel - Swing metrics display and recommendations
"""

import customtkinter as ctk
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MetricsPanel(ctk.CTkFrame):
    """Metrics sidebar with swing analysis data"""
    
    def __init__(self, parent, colors: Dict[str, str]):
        super().__init__(parent, fg_color=colors['bg_main'], width=320, corner_radius=0)
        self.colors = colors
        
        # State
        self.metrics_data: Dict = {}
        self.recommendations: List[Tuple[str, str]] = []
        
        # UI components
        self.metrics_container: Optional[ctk.CTkScrollableFrame] = None
        self.recommendations_container: Optional[ctk.CTkScrollableFrame] = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create metrics panel widgets"""
        # Don't pack here - parent will use grid
        # self.pack(side='right', fill='y', padx=0, pady=0)
        self.pack_propagate(False)
        
        # Border
        border = ctk.CTkFrame(self, fg_color=self.colors['border'], width=1)
        border.pack(side='left', fill='y')
        
        # Content
        content = ctk.CTkScrollableFrame(self, fg_color=self.colors['bg_main'])
        content.pack(side='left', fill='both', expand=True, padx=24, pady=24)
        
        # Header
        header = ctk.CTkLabel(
            content,
            text="SWING ANALYSIS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        header.pack(anchor='w', pady=(0, 24))
        
        # Metrics container
        self.metrics_container = ctk.CTkScrollableFrame(
            content,
            fg_color=self.colors['bg_main']
        )
        self.metrics_container.pack(fill='both', expand=True)
        
        # Initial metrics
        self.update_metrics_display()
        
        # Recommendations header
        rec_header = ctk.CTkLabel(
            content,
            text="KEY RECOMMENDATIONS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        rec_header.pack(anchor='w', pady=(32, 24))
        
        # Recommendations container
        self.recommendations_container = ctk.CTkScrollableFrame(
            content,
            fg_color=self.colors['bg_main']
        )
        self.recommendations_container.pack(fill='both', expand=True)
        
        # Initial recommendations
        self.update_recommendations_display()
    
    def update_metrics_display(self):
        """Update metrics display"""
        if not self.metrics_container:
            return
        
        # Clear existing metrics
        for widget in self.metrics_container.winfo_children():
            widget.destroy()
        
        # Display metrics
        if self.metrics_data:
            for name, data in self.metrics_data.items():
                self.create_metric_item(self.metrics_container, name, data)
        else:
            # Placeholder
            placeholder = ctk.CTkLabel(
                self.metrics_container,
                text="No metrics available.\nStart a session to see analysis.",
                font=ctk.CTkFont(size=10),
                text_color=self.colors['text_dim'],
                justify='left'
            )
            placeholder.pack(pady=20)
    
    def create_metric_item(self, parent, name: str, data: Dict):
        """Create a metric display item"""
        item = ctk.CTkFrame(
            parent,
            fg_color=self.colors['bg_panel'],
            corner_radius=4
        )
        item.pack(fill='x', pady=6)
        
        content = ctk.CTkFrame(item, fg_color="transparent")
        content.pack(fill='both', padx=16, pady=16)
        
        # Name
        name_label = ctk.CTkLabel(
            content,
            text=name.upper(),
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color=self.colors['text_dim']
        )
        name_label.pack(anchor='w')
        
        # Value frame
        value_frame = ctk.CTkFrame(content, fg_color="transparent")
        value_frame.pack(anchor='w', pady=(8, 4))
        
        value = data.get('value', 'N/A')
        unit = data.get('unit', '')
        
        value_label = ctk.CTkLabel(
            value_frame,
            text=str(value),
            font=ctk.CTkFont(size=24),
            text_color=self.colors['text_primary']
        )
        value_label.pack(side='left')
        
        if unit:
            unit_label = ctk.CTkLabel(
                value_frame,
                text=unit,
                font=ctk.CTkFont(size=10),
                text_color=self.colors['text_dim']
            )
            unit_label.pack(side='left', padx=(4, 0))
        
        # Comparison
        comp_frame = ctk.CTkFrame(content, fg_color="transparent")
        comp_frame.pack(anchor='w')
        
        pro_val = data.get('pro', 'N/A')
        pro_label = ctk.CTkLabel(
            comp_frame,
            text=f"Pro: {pro_val}",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_secondary']
        )
        pro_label.pack(side='left')
        
        # Diff badge
        diff = data.get('diff', 'N/A')
        status = data.get('status', 'warning')
        
        diff_color = {
            'good': self.colors['good'],
            'warning': self.colors['warning'],
            'bad': self.colors['bad']
        }.get(status, self.colors['text_dim'])
        
        diff_label = ctk.CTkLabel(
            comp_frame,
            text=str(diff),
            font=ctk.CTkFont(size=9),
            fg_color=self.colors['bg_main'],
            text_color=diff_color,
            corner_radius=4,
            padx=8,
            pady=2
        )
        diff_label.pack(side='left', padx=(8, 0))
    
    def update_recommendations_display(self):
        """Update recommendations display"""
        if not self.recommendations_container:
            return
        
        # Clear existing recommendations
        for widget in self.recommendations_container.winfo_children():
            widget.destroy()
        
        # Display recommendations
        if self.recommendations:
            for title, text in self.recommendations:
                self.create_recommendation_item(self.recommendations_container, title, text)
        else:
            placeholder = ctk.CTkLabel(
                self.recommendations_container,
                text="No recommendations yet.\nAnalyze a swing to get personalized feedback.",
                font=ctk.CTkFont(size=10),
                text_color=self.colors['text_dim'],
                justify='left'
            )
            placeholder.pack(pady=20)
    
    def create_recommendation_item(self, parent, title: str, text: str):
        """Create a recommendation item"""
        item = ctk.CTkFrame(
            parent,
            fg_color=self.colors['bg_panel'],
            corner_radius=4
        )
        item.pack(fill='x', pady=6)
        
        content = ctk.CTkFrame(item, fg_color="transparent")
        content.pack(fill='both', padx=16, pady=16)
        
        title_label = ctk.CTkLabel(
            content,
            text=title.upper(),
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color=self.colors['text_dim']
        )
        title_label.pack(anchor='w')
        
        text_label = ctk.CTkLabel(
            content,
            text=text,
            font=ctk.CTkFont(size=10),
            text_color=self.colors['text_primary'],
            wraplength=250,
            justify='left'
        )
        text_label.pack(anchor='w', pady=(8, 0))
    
    def set_metrics(self, metrics: Dict):
        """Set metrics data"""
        self.metrics_data = metrics
        self.update_metrics_display()
    
    def set_recommendations(self, recommendations: List[Tuple[str, str]]):
        """Set recommendations"""
        self.recommendations = recommendations
        self.update_recommendations_display()
    
    def update_swing_data(self, swing_data: Dict):
        """Update metrics and recommendations from swing data (optimized for performance)"""
        # Extract metrics from swing_data
        metrics = swing_data.get('metrics', {})
        flaw_analysis = swing_data.get('flaw_analysis', {})
        pro_match = swing_data.get('pro_match', {})
        pro_metrics = pro_match.get('metrics', {})
        
        # Convert metrics to display format (optimized: only process numeric metrics)
        display_metrics = {}
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                pro_value = pro_metrics.get(key, value)
                diff = value - pro_value
                display_metrics[key.replace('_', ' ').title()] = {
                    'value': f"{value:.1f}",
                    'unit': self._get_unit_for_metric(key),
                    'pro': f"{pro_value:.1f}" if isinstance(pro_value, (int, float)) else 'N/A',
                    'diff': f"{diff:.1f}",
                    'status': 'good' if abs(diff) < 5 else 'warning'
                }
        
        # Limit to top 20 metrics for performance
        if len(display_metrics) > 20:
            # Sort by absolute difference and take top 20
            sorted_metrics = sorted(
                display_metrics.items(),
                key=lambda x: abs(float(x[1].get('diff', 0))),
                reverse=True
            )[:20]
            display_metrics = dict(sorted_metrics)
        
        self.set_metrics(display_metrics)
        
        # Extract recommendations from flaw analysis (limit to top 3)
        flaws = flaw_analysis.get('flaws', [])
        recommendations = []
        sorted_flaws = sorted(flaws, key=lambda x: x.get('severity', 0), reverse=True)[:3]
        for i, flaw in enumerate(sorted_flaws, 1):
            metric_name = flaw.get('metric', 'Unknown').replace('_', ' ').title()
            recommendation = flaw.get('recommendation', 'No specific recommendation available.')
            recommendations.append((f"Priority {i}", f"{metric_name}: {recommendation}"))
        
        if not recommendations:
            recommendations = [("Great Job!", "No significant flaws detected. Keep practicing to maintain consistency.")]
        
        self.set_recommendations(recommendations)
    
    def _get_unit_for_metric(self, metric_key: str) -> str:
        """Get unit for a metric key"""
        units = {
            'hip_rotation_top': 'deg',
            'hip_rotation': 'deg',
            'shoulder_rotation_top': 'deg',
            'shoulder_turn': 'deg',
            'shoulder_rotation': 'deg',
            'x_factor': 'deg',
            'spine_angle_address': 'deg',
            'spine_angle': 'deg',
            'spine_angle_change': 'deg',
            'tempo_ratio': ':1',
            'weight_transfer': '%',
            'weight_shift': '%',
            'club_speed': 'mph',
            'ball_speed': 'mph',
            'backswing_time': 's',
            'downswing_time': 's'
        }
        return units.get(metric_key.lower(), '')
    
    def clear_display(self):
        """Clear metrics and recommendations display"""
        self.metrics_data = {}
        self.recommendations = []
        self.update_metrics_display()
        self.update_recommendations_display()

