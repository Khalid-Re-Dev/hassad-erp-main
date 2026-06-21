"""
Charts Utilities Module

Provides reusable chart components and utilities for data visualization
in the Hassad ERP dashboard and reporting modules.

Features:
- Line charts (trends, time series)
- Bar charts (comparisons, rankings)
- Pie charts (distributions, percentages)
- Area charts (cumulative data)
- Theme support (Light/Dark)
- RTL compatibility
- Export capabilities

Phase: F2.5 - Dashboard Analytics Modernization
Version: 1.0.0
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from decimal import Decimal

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# Matplotlib integration with PyQt6
import matplotlib
matplotlib.use('Qt5Agg')  # Backend for PyQt integration
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# CHART THEMES AND STYLES
# ============================================================================

class ChartTheme(Enum):
    """Chart theme presets."""
    LIGHT = "light"
    DARK = "dark"
    MODERN = "modern"
    PROFESSIONAL = "professional"


class ChartStyle(Enum):
    """Chart style variants."""
    DEFAULT = "default"
    MINIMAL = "minimal"
    DETAILED = "detailed"


# Color palettes
COLOR_PALETTES = {
    ChartTheme.LIGHT: {
        'primary': '#3498db',
        'secondary': '#2ecc71',
        'accent': '#e74c3c',
        'warning': '#f39c12',
        'info': '#9b59b6',
        'background': '#ffffff',
        'text': '#2c3e50',
        'grid': '#ecf0f1',
        'series': ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
    },
    ChartTheme.DARK: {
        'primary': '#5dade2',
        'secondary': '#58d68d',
        'accent': '#ec7063',
        'warning': '#f5b041',
        'info': '#bb8fce',
        'background': '#2c3e50',
        'text': '#ecf0f1',
        'grid': '#34495e',
        'series': ['#5dade2', '#58d68d', '#ec7063', '#f5b041', '#bb8fce', '#48c9b0']
    },
    ChartTheme.MODERN: {
        'primary': '#667eea',
        'secondary': '#f093fb',
        'accent': '#fa709a',
        'warning': '#feca57',
        'info': '#48dbfb',
        'background': '#ffffff',
        'text': '#2d3436',
        'grid': '#dfe6e9',
        'series': ['#667eea', '#f093fb', '#fa709a', '#feca57', '#48dbfb', '#0abde3']
    },
    ChartTheme.PROFESSIONAL: {
        'primary': '#34495e',
        'secondary': '#16a085',
        'accent': '#c0392b',
        'warning': '#d35400',
        'info': '#2980b9',
        'background': '#ffffff',
        'text': '#2c3e50',
        'grid': '#bdc3c7',
        'series': ['#34495e', '#16a085', '#c0392b', '#d35400', '#2980b9', '#8e44ad']
    }
}


# ============================================================================
# BASE CHART WIDGET
# ============================================================================

class ChartWidget(QWidget):
    """
    Base chart widget with matplotlib integration.
    
    Provides common functionality for all chart types:
    - Matplotlib canvas integration
    - Theme support
    - Responsive sizing
    - Export capabilities
    """
    
    def __init__(self, theme: ChartTheme = ChartTheme.MODERN, parent: Optional[QWidget] = None):
        """
        Initialize chart widget.
        
        Args:
            theme: Chart theme to use
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.theme = theme
        self.colors = COLOR_PALETTES[theme]
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor(self.colors['background'])
        
        # Create canvas
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        logger.debug(f"ChartWidget initialized with theme: {theme.value}")
    
    def get_axes(self):
        """Get or create main axes."""
        if not self.figure.axes:
            ax = self.figure.add_subplot(111)
            self._style_axes(ax)
            return ax
        return self.figure.axes[0]
    
    def _style_axes(self, ax):
        """Apply theme styling to axes."""
        ax.set_facecolor(self.colors['background'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(self.colors['grid'])
        ax.spines['bottom'].set_color(self.colors['grid'])
        ax.tick_params(colors=self.colors['text'], which='both')
        ax.grid(True, alpha=0.3, color=self.colors['grid'], linestyle='--', linewidth=0.5)
        
        # Set text colors
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color(self.colors['text'])
    
    def clear(self):
        """Clear figure."""
        self.figure.clear()
    
    def refresh(self):
        """Refresh canvas."""
        self.canvas.draw()
        self.canvas.flush_events()
    
    def export_to_file(self, filepath: str, dpi: int = 300):
        """
        Export chart to file.
        
        Args:
            filepath: Output file path (supports .png, .jpg, .pdf, .svg)
            dpi: Resolution in dots per inch
        """
        self.figure.savefig(filepath, dpi=dpi, bbox_inches='tight', 
                           facecolor=self.colors['background'])
        logger.info(f"Chart exported to: {filepath}")


# ============================================================================
# LINE CHART
# ============================================================================

def create_line_chart(
    data: List[Dict[str, Any]],
    x_key: str,
    y_key: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    theme: ChartTheme = ChartTheme.MODERN,
    show_markers: bool = True,
    show_values: bool = False,
    parent: Optional[QWidget] = None
) -> ChartWidget:
    """
    Create line chart for trend visualization.
    
    Args:
        data: List of dictionaries with x and y values
        x_key: Key for x-axis values
        y_key: Key for y-axis values
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        theme: Chart theme
        show_markers: Whether to show data point markers
        show_values: Whether to display values on points
        parent: Parent widget
        
    Returns:
        ChartWidget with line chart
        
    Example:
        >>> data = [
        ...     {'date': '01/15', 'value': 1250.50},
        ...     {'date': '01/16', 'value': 1380.75},
        ... ]
        >>> chart = create_line_chart(data, 'date', 'value', title="Sales Trend")
    """
    widget = ChartWidget(theme=theme, parent=parent)
    colors = widget.colors
    
    try:
        ax = widget.get_axes()
        
        # Extract data
        x_values = [item[x_key] for item in data]
        y_values = [float(item[y_key]) for item in data]
        
        # Plot line
        line = ax.plot(
            x_values, y_values,
            color=colors['primary'],
            linewidth=2.5,
            marker='o' if show_markers else None,
            markersize=8 if show_markers else 0,
            markerfacecolor=colors['primary'],
            markeredgecolor='white',
            markeredgewidth=2
        )[0]
        
        # Fill area under line
        ax.fill_between(x_values, y_values, alpha=0.2, color=colors['primary'])
        
        # Add value labels
        if show_values:
            for i, (x, y) in enumerate(zip(x_values, y_values)):
                ax.annotate(
                    f'${y:,.0f}' if y >= 1000 else f'${y:.2f}',
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center',
                    fontsize=9,
                    color=colors['text'],
                    weight='bold'
                )
        
        # Set labels and title
        if title:
            ax.set_title(title, fontsize=14, weight='bold', color=colors['text'], pad=15)
        if x_label:
            ax.set_xlabel(x_label, fontsize=11, color=colors['text'], weight='600')
        if y_label:
            ax.set_ylabel(y_label, fontsize=11, color=colors['text'], weight='600')
        
        # Rotate x-axis labels for better readability
        ax.tick_params(axis='x', rotation=45)
        
        # Tight layout
        widget.figure.tight_layout()
        widget.refresh()
        
        logger.debug(f"Line chart created with {len(data)} data points")
        
    except Exception as e:
        logger.error(f"Error creating line chart: {e}", exc_info=True)
        raise
    
    return widget


# ============================================================================
# BAR CHART
# ============================================================================

def create_bar_chart(
    data: List[Dict[str, Any]],
    x_key: str,
    y_key: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    theme: ChartTheme = ChartTheme.MODERN,
    horizontal: bool = False,
    show_values: bool = True,
    parent: Optional[QWidget] = None
) -> ChartWidget:
    """
    Create bar chart for comparisons.
    
    Args:
        data: List of dictionaries with x and y values
        x_key: Key for category names
        y_key: Key for values
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        theme: Chart theme
        horizontal: Whether to create horizontal bars
        show_values: Whether to display values on bars
        parent: Parent widget
        
    Returns:
        ChartWidget with bar chart
        
    Example:
        >>> data = [
        ...     {'product': 'Product A', 'sales': 5200},
        ...     {'product': 'Product B', 'sales': 4100},
        ... ]
        >>> chart = create_bar_chart(data, 'product', 'sales', title="Top Products")
    """
    widget = ChartWidget(theme=theme, parent=parent)
    colors = widget.colors
    
    try:
        ax = widget.get_axes()
        
        # Extract data
        categories = [str(item[x_key]) for item in data]
        values = [float(item[y_key]) for item in data]
        
        # Create color gradient
        bar_colors = [colors['series'][i % len(colors['series'])] for i in range(len(data))]
        
        # Plot bars
        if horizontal:
            bars = ax.barh(categories, values, color=bar_colors, edgecolor='white', linewidth=1.5)
        else:
            bars = ax.bar(categories, values, color=bar_colors, edgecolor='white', linewidth=1.5)
        
        # Add value labels
        if show_values:
            for i, (cat, val) in enumerate(zip(categories, values)):
                if horizontal:
                    ax.text(val, i, f' ${val:,.0f}' if val >= 1000 else f' ${val:.2f}',
                           va='center', ha='left', fontsize=10, weight='bold', color=colors['text'])
                else:
                    ax.text(i, val, f'${val:,.0f}' if val >= 1000 else f'${val:.2f}',
                           ha='center', va='bottom', fontsize=10, weight='bold', color=colors['text'])
        
        # Set labels and title
        if title:
            ax.set_title(title, fontsize=14, weight='bold', color=colors['text'], pad=15)
        if x_label:
            ax.set_xlabel(x_label, fontsize=11, color=colors['text'], weight='600')
        if y_label:
            ax.set_ylabel(y_label, fontsize=11, color=colors['text'], weight='600')
        
        # Rotate labels if needed
        if not horizontal:
            ax.tick_params(axis='x', rotation=45)
        
        # Tight layout
        widget.figure.tight_layout()
        widget.refresh()
        
        logger.debug(f"Bar chart created with {len(data)} bars")
        
    except Exception as e:
        logger.error(f"Error creating bar chart: {e}", exc_info=True)
        raise
    
    return widget


# ============================================================================
# PIE CHART
# ============================================================================

def create_pie_chart(
    data: List[Dict[str, Any]],
    label_key: str,
    value_key: str,
    title: str = "",
    theme: ChartTheme = ChartTheme.MODERN,
    show_percentage: bool = True,
    explode_max: bool = True,
    parent: Optional[QWidget] = None
) -> ChartWidget:
    """
    Create pie chart for distribution visualization.
    
    Args:
        data: List of dictionaries with labels and values
        label_key: Key for slice labels
        value_key: Key for slice values
        title: Chart title
        theme: Chart theme
        show_percentage: Whether to show percentages
        explode_max: Whether to explode the largest slice
        parent: Parent widget
        
    Returns:
        ChartWidget with pie chart
        
    Example:
        >>> data = [
        ...     {'method': 'CASH', 'total': 12500},
        ...     {'method': 'CARD', 'total': 8200},
        ... ]
        >>> chart = create_pie_chart(data, 'method', 'total', title="Payment Methods")
    """
    widget = ChartWidget(theme=theme, parent=parent)
    colors = widget.colors
    
    try:
        ax = widget.get_axes()
        
        # Extract data
        labels = [str(item[label_key]) for item in data]
        values = [float(item[value_key]) for item in data]
        
        # Create explode effect for largest slice
        explode = [0] * len(values)
        if explode_max and values:
            max_idx = values.index(max(values))
            explode[max_idx] = 0.1
        
        # Pie colors
        pie_colors = [colors['series'][i % len(colors['series'])] for i in range(len(data))]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%' if show_percentage else None,
            startangle=90,
            colors=pie_colors,
            explode=explode,
            shadow=True,
            textprops={'color': colors['text'], 'weight': 'bold', 'fontsize': 10}
        )
        
        # Style percentage text
        if show_percentage:
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
                autotext.set_weight('bold')
        
        # Equal aspect ratio ensures circular pie
        ax.axis('equal')
        
        # Add title
        if title:
            ax.set_title(title, fontsize=14, weight='bold', color=colors['text'], pad=15)
        
        # Add legend
        ax.legend(
            wedges, labels,
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            frameon=False,
            fontsize=10
        )
        
        # Tight layout
        widget.figure.tight_layout()
        widget.refresh()
        
        logger.debug(f"Pie chart created with {len(data)} slices")
        
    except Exception as e:
        logger.error(f"Error creating pie chart: {e}", exc_info=True)
        raise
    
    return widget


# ============================================================================
# AREA CHART
# ============================================================================

def create_area_chart(
    data: List[Dict[str, Any]],
    x_key: str,
    y_key: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    theme: ChartTheme = ChartTheme.MODERN,
    stacked: bool = False,
    parent: Optional[QWidget] = None
) -> ChartWidget:
    """
    Create area chart for cumulative data visualization.
    
    Args:
        data: List of dictionaries with x and y values
        x_key: Key for x-axis values
        y_key: Key for y-axis values (or list of keys for multiple series)
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        theme: Chart theme
        stacked: Whether to stack multiple series
        parent: Parent widget
        
    Returns:
        ChartWidget with area chart
    """
    widget = ChartWidget(theme=theme, parent=parent)
    colors = widget.colors
    
    try:
        ax = widget.get_axes()
        
        # Extract data
        x_values = [item[x_key] for item in data]
        y_values = [float(item[y_key]) for item in data]
        
        # Create area chart
        ax.fill_between(
            x_values, y_values,
            alpha=0.4,
            color=colors['primary'],
            edgecolor=colors['primary'],
            linewidth=2
        )
        
        # Add line on top
        ax.plot(x_values, y_values, color=colors['primary'], linewidth=2, marker='o', markersize=6)
        
        # Set labels and title
        if title:
            ax.set_title(title, fontsize=14, weight='bold', color=colors['text'], pad=15)
        if x_label:
            ax.set_xlabel(x_label, fontsize=11, color=colors['text'], weight='600')
        if y_label:
            ax.set_ylabel(y_label, fontsize=11, color=colors['text'], weight='600')
        
        # Rotate x-axis labels
        ax.tick_params(axis='x', rotation=45)
        
        # Tight layout
        widget.figure.tight_layout()
        widget.refresh()
        
        logger.debug(f"Area chart created with {len(data)} data points")
        
    except Exception as e:
        logger.error(f"Error creating area chart: {e}", exc_info=True)
        raise
    
    return widget


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_currency(value: float, currency_symbol: str = "$") -> str:
    """
    Format value as currency string.
    
    Args:
        value: Numeric value
        currency_symbol: Currency symbol to use
        
    Returns:
        Formatted currency string
    """
    if value >= 1000000:
        return f"{currency_symbol}{value/1000000:.1f}M"
    elif value >= 1000:
        return f"{currency_symbol}{value/1000:.1f}K"
    else:
        return f"{currency_symbol}{value:.2f}"


def calculate_trend(current: float, previous: float) -> Tuple[float, str]:
    """
    Calculate trend percentage and direction.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Tuple of (percentage_change, direction)
        direction is one of: 'up', 'down', 'flat'
    """
    if previous == 0:
        return (0.0, 'flat')
    
    change = ((current - previous) / previous) * 100
    
    if change > 0.5:
        direction = 'up'
    elif change < -0.5:
        direction = 'down'
    else:
        direction = 'flat'
    
    return (change, direction)


def aggregate_data(
    data: List[Dict[str, Any]],
    group_key: str,
    value_key: str,
    aggregation: str = 'sum'
) -> List[Dict[str, Any]]:
    """
    Aggregate data by group key.
    
    Args:
        data: Input data list
        group_key: Key to group by
        value_key: Key to aggregate
        aggregation: Aggregation function ('sum', 'avg', 'count', 'min', 'max')
        
    Returns:
        Aggregated data list
    """
    from collections import defaultdict
    
    groups = defaultdict(list)
    
    # Group data
    for item in data:
        groups[item[group_key]].append(float(item[value_key]))
    
    # Aggregate
    result = []
    for group, values in groups.items():
        if aggregation == 'sum':
            agg_value = sum(values)
        elif aggregation == 'avg':
            agg_value = sum(values) / len(values)
        elif aggregation == 'count':
            agg_value = len(values)
        elif aggregation == 'min':
            agg_value = min(values)
        elif aggregation == 'max':
            agg_value = max(values)
        else:
            agg_value = sum(values)
        
        result.append({
            group_key: group,
            value_key: agg_value
        })
    
    return result


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

logger.info("=" * 70)
logger.info("Charts Utilities Module Loaded")
logger.info(f"Available chart types: Line, Bar, Pie, Area")
logger.info(f"Available themes: {[t.value for t in ChartTheme]}")
logger.info("=" * 70)
