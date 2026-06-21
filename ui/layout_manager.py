"""
Layout Manager for Hassad ERP
===============================

Centralized layout management system providing:
- Standard layout patterns (CRUD, List-Detail, Dashboard, Form)
- Layout helper utilities
- Responsive behavior management
- Theme integration
- RTL/LTR layout adaptation

Phase: F2.2 - Layout System Architecture
Version: 1.0.0
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from enum import Enum

from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QSizePolicy
)

from ui.layout_components import (
    Card, Panel, Section, SplitView, Toolbar, FormSection,
    DataHeader, FilterBar, Spacing
)

# Configure logging
logger = logging.getLogger(__name__)
layout_logger = logging.getLogger('layout_engine')


# ============================================================================
# LAYOUT PATTERNS ENUM
# ============================================================================

class LayoutPattern(Enum):
    """Standard layout patterns."""
    CRUD = "crud"                    # Table with toolbar
    LIST_DETAIL = "list_detail"      # Split view with list and detail
    DASHBOARD = "dashboard"          # Grid of cards
    FORM = "form"                    # Multi-section form
    REPORT = "report"                # Header + filters + data
    MASTER_DETAIL = "master_detail"  # Tree/table + detail panel
    WIZARD = "wizard"                # Step-by-step flow
    SETTINGS = "settings"            # Tabbed or sectioned settings


# ============================================================================
# LAYOUT MANAGER CLASS
# ============================================================================

class LayoutManager(QObject):
    """
    Centralized layout management system.
    
    Provides standard layouts and helper utilities for consistent UI construction.
    
    Features:
    - Standard layout pattern generation
    - Responsive layout utilities
    - Spacing and sizing helpers
    - RTL-aware layout construction
    - Theme integration
    """
    
    layout_created = pyqtSignal(str, QWidget)  # (pattern_name, widget)
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize layout manager.
        
        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self._layouts_created = []
        layout_logger.info("LayoutManager initialized")
    
    # ========================================================================
    # PATTERN CREATION METHODS
    # ========================================================================
    
    def create_crud_layout(self, parent: Optional[QWidget] = None) -> Tuple[QWidget, Dict[str, Any]]:
        """
        Create CRUD (Create, Read, Update, Delete) layout pattern.
        
        Structure:
        - Toolbar at top (actions: Add, Edit, Delete, Refresh)
        - Filter bar
        - Main data view (table/cards)
        
        Args:
            parent: Parent widget
            
        Returns:
            Tuple of (widget, components_dict)
        """
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Spacing.MEDIUM.value, Spacing.MEDIUM.value,
                                  Spacing.MEDIUM.value, Spacing.MEDIUM.value)
        layout.setSpacing(Spacing.SMALL.value)
        
        # Toolbar
        toolbar = Toolbar()
        layout.addWidget(toolbar)
        
        # Filter bar
        filter_bar = FilterBar()
        layout.addWidget(filter_bar)
        
        # Data view container (to be filled by caller)
        data_container = QWidget()
        data_layout = QVBoxLayout(data_container)
        data_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(data_container, 1)  # Stretch factor 1
        
        components = {
            'toolbar': toolbar,
            'filter_bar': filter_bar,
            'data_container': data_container,
            'data_layout': data_layout
        }
        
        layout_logger.info("CRUD layout created")
        self.layout_created.emit("crud", container)
        
        return container, components
    
    def create_list_detail_layout(self, parent: Optional[QWidget] = None,
                                   split_ratio: Tuple[float, float] = (0.4, 0.6)) -> Tuple[QWidget, Dict[str, Any]]:
        """
        Create List-Detail layout pattern.
        
        Structure:
        - Left: List view with filter
        - Right: Detail view with actions
        
        Args:
            parent: Parent widget
            split_ratio: (left_ratio, right_ratio) for split sizes
            
        Returns:
            Tuple of (widget, components_dict)
        """
        container = QWidget(parent)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Split view
        split_view = SplitView(Qt.Orientation.Horizontal)
        
        # Left panel (list)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(Spacing.MEDIUM.value, Spacing.MEDIUM.value,
                                       Spacing.SMALL.value, Spacing.MEDIUM.value)
        left_layout.setSpacing(Spacing.SMALL.value)
        
        list_filter = FilterBar()
        left_layout.addWidget(list_filter)
        
        list_container = QWidget()
        list_container_layout = QVBoxLayout(list_container)
        list_container_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(list_container, 1)
        
        # Right panel (detail)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(Spacing.SMALL.value, Spacing.MEDIUM.value,
                                        Spacing.MEDIUM.value, Spacing.MEDIUM.value)
        right_layout.setSpacing(Spacing.MEDIUM.value)
        
        detail_header = DataHeader("Detail View | عرض التفاصيل")
        right_layout.addWidget(detail_header)
        
        detail_container = QWidget()
        detail_container_layout = QVBoxLayout(detail_container)
        detail_container_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(detail_container, 1)
        
        # Add to split view
        split_view.addWidget(left_panel)
        split_view.addWidget(right_panel)
        split_view.set_sizes_ratio(split_ratio[0], split_ratio[1])
        
        main_layout.addWidget(split_view)
        
        components = {
            'split_view': split_view,
            'left_panel': left_panel,
            'right_panel': right_panel,
            'list_filter': list_filter,
            'list_container': list_container,
            'detail_header': detail_header,
            'detail_container': detail_container
        }
        
        layout_logger.info(f"List-Detail layout created with ratio {split_ratio}")
        self.layout_created.emit("list_detail", container)
        
        return container, components
    
    def create_dashboard_layout(self, parent: Optional[QWidget] = None,
                                 grid_columns: int = 3) -> Tuple[QWidget, Dict[str, Any]]:
        """
        Create Dashboard layout pattern.
        
        Structure:
        - Header with title and actions
        - Grid of cards/widgets
        
        Args:
            parent: Parent widget
            grid_columns: Number of columns in grid
            
        Returns:
            Tuple of (widget, components_dict)
        """
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Spacing.LARGE.value, Spacing.LARGE.value,
                                  Spacing.LARGE.value, Spacing.LARGE.value)
        layout.setSpacing(Spacing.MEDIUM.value)
        
        # Header
        header = DataHeader("Dashboard | لوحة المعلومات", "Welcome back | مرحباً بعودتك")
        layout.addWidget(header)
        
        # Scroll area for grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Grid container
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(Spacing.MEDIUM.value)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(grid_widget)
        layout.addWidget(scroll_area, 1)
        
        components = {
            'header': header,
            'scroll_area': scroll_area,
            'grid_widget': grid_widget,
            'grid_layout': grid_layout,
            'grid_columns': grid_columns,
            '_current_row': 0,
            '_current_col': 0
        }
        
        layout_logger.info(f"Dashboard layout created with {grid_columns} columns")
        self.layout_created.emit("dashboard", container)
        
        return container, components
    
    def create_form_layout(self, parent: Optional[QWidget] = None,
                           sections: Optional[List[str]] = None) -> Tuple[QWidget, Dict[str, Any]]:
        """
        Create Form layout pattern.
        
        Structure:
        - Header with title
        - Multiple collapsible sections
        - Footer with actions (Save, Cancel)
        
        Args:
            parent: Parent widget
            sections: List of section names
            
        Returns:
            Tuple of (widget, components_dict)
        """
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Spacing.LARGE.value, Spacing.LARGE.value,
                                  Spacing.LARGE.value, Spacing.LARGE.value)
        layout.setSpacing(Spacing.MEDIUM.value)
        
        # Header
        header = DataHeader("Form | نموذج")
        layout.addWidget(header)
        
        # Scroll area for form sections
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Form container
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(Spacing.MEDIUM.value)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create sections if provided
        section_widgets = {}
        if sections:
            for section_name in sections:
                section = FormSection(section_name, columns=2)
                form_layout.addWidget(section)
                section_widgets[section_name] = section
        
        form_layout.addStretch()
        scroll_area.setWidget(form_widget)
        layout.addWidget(scroll_area, 1)
        
        # Footer with actions
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, Spacing.MEDIUM.value, 0, 0)
        footer_layout.addStretch()
        layout.addWidget(footer)
        
        components = {
            'header': header,
            'scroll_area': scroll_area,
            'form_widget': form_widget,
            'form_layout': form_layout,
            'sections': section_widgets,
            'footer': footer,
            'footer_layout': footer_layout
        }
        
        layout_logger.info(f"Form layout created with {len(sections or [])} sections")
        self.layout_created.emit("form", container)
        
        return container, components
    
    def create_report_layout(self, parent: Optional[QWidget] = None) -> Tuple[QWidget, Dict[str, Any]]:
        """
        Create Report layout pattern.
        
        Structure:
        - Header with title and export actions
        - Filter panel (collapsible)
        - Report data view
        - Summary footer
        
        Args:
            parent: Parent widget
            
        Returns:
            Tuple of (widget, components_dict)
        """
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Spacing.MEDIUM.value, Spacing.MEDIUM.value,
                                  Spacing.MEDIUM.value, Spacing.MEDIUM.value)
        layout.setSpacing(Spacing.SMALL.value)
        
        # Header
        header = DataHeader("Report | تقرير")
        layout.addWidget(header)
        
        # Filter panel (collapsible)
        filter_panel = Panel("Filters | المرشحات", expanded=True)
        layout.addWidget(filter_panel)
        
        # Report data container
        report_container = QWidget()
        report_layout = QVBoxLayout(report_container)
        report_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(report_container, 1)
        
        # Summary footer
        summary = QWidget()
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(0, Spacing.MEDIUM.value, 0, 0)
        layout.addWidget(summary)
        
        components = {
            'header': header,
            'filter_panel': filter_panel,
            'report_container': report_container,
            'report_layout': report_layout,
            'summary': summary,
            'summary_layout': summary_layout
        }
        
        layout_logger.info("Report layout created")
        self.layout_created.emit("report", container)
        
        return container, components
    
    # ========================================================================
    # HELPER UTILITIES
    # ========================================================================
    
    def add_card_to_grid(self, grid_layout: QGridLayout, card: Card, 
                         row: int, col: int, row_span: int = 1, col_span: int = 1):
        """
        Add card to grid layout.
        
        Args:
            grid_layout: Target grid layout
            card: Card widget
            row: Row position
            col: Column position
            row_span: Number of rows to span
            col_span: Number of columns to span
        """
        grid_layout.addWidget(card, row, col, row_span, col_span)
        layout_logger.debug(f"Card added to grid at ({row}, {col})")
    
    def create_scrollable_container(self, widget: QWidget) -> QScrollArea:
        """
        Wrap widget in scrollable container.
        
        Args:
            widget: Widget to make scrollable
            
        Returns:
            QScrollArea containing widget
        """
        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        return scroll_area
    
    def apply_standard_margins(self, layout, size: Spacing = Spacing.MEDIUM):
        """
        Apply standard margins to layout.
        
        Args:
            layout: Layout to modify
            size: Spacing size
        """
        value = size.value
        layout.setContentsMargins(value, value, value, value)
    
    def apply_standard_spacing(self, layout, size: Spacing = Spacing.SMALL):
        """
        Apply standard spacing to layout.
        
        Args:
            layout: Layout to modify
            size: Spacing size
        """
        layout.setSpacing(size.value)
    
    def create_two_column_layout(self) -> Tuple[QHBoxLayout, QVBoxLayout, QVBoxLayout]:
        """
        Create standard two-column layout.
        
        Returns:
            Tuple of (main_layout, left_column, right_column)
        """
        main_layout = QHBoxLayout()
        main_layout.setSpacing(Spacing.MEDIUM.value)
        
        left_column = QVBoxLayout()
        left_column.setSpacing(Spacing.SMALL.value)
        
        right_column = QVBoxLayout()
        right_column.setSpacing(Spacing.SMALL.value)
        
        main_layout.addLayout(left_column, 1)
        main_layout.addLayout(right_column, 1)
        
        return main_layout, left_column, right_column
    
    def create_three_column_layout(self) -> Tuple[QHBoxLayout, QVBoxLayout, QVBoxLayout, QVBoxLayout]:
        """
        Create standard three-column layout.
        
        Returns:
            Tuple of (main_layout, left, center, right)
        """
        main_layout = QHBoxLayout()
        main_layout.setSpacing(Spacing.MEDIUM.value)
        
        left = QVBoxLayout()
        left.setSpacing(Spacing.SMALL.value)
        
        center = QVBoxLayout()
        center.setSpacing(Spacing.SMALL.value)
        
        right = QVBoxLayout()
        right.setSpacing(Spacing.SMALL.value)
        
        main_layout.addLayout(left, 1)
        main_layout.addLayout(center, 1)
        main_layout.addLayout(right, 1)
        
        return main_layout, left, center, right
    
    def get_standard_card_size(self) -> Tuple[int, int]:
        """
        Get standard card size.
        
        Returns:
            Tuple of (width, height)
        """
        return (300, 200)
    
    def get_standard_panel_width(self) -> int:
        """
        Get standard panel width for side panels.
        
        Returns:
            Width in pixels
        """
        return 300


# ============================================================================
# GLOBAL LAYOUT MANAGER INSTANCE
# ============================================================================

_layout_manager_instance: Optional[LayoutManager] = None

def get_layout_manager() -> LayoutManager:
    """
    Get global LayoutManager instance (singleton pattern).
    
    Returns:
        LayoutManager instance
    """
    global _layout_manager_instance
    
    if _layout_manager_instance is None:
        _layout_manager_instance = LayoutManager()
        layout_logger.info("Created global LayoutManager instance")
    
    return _layout_manager_instance


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_layout(pattern: LayoutPattern, parent: Optional[QWidget] = None, **kwargs) -> Tuple[QWidget, Dict[str, Any]]:
    """
    Convenience function to create layout by pattern.
    
    Args:
        pattern: Layout pattern to create
        parent: Parent widget
        **kwargs: Pattern-specific arguments
        
    Returns:
        Tuple of (widget, components_dict)
    """
    manager = get_layout_manager()
    
    if pattern == LayoutPattern.CRUD:
        return manager.create_crud_layout(parent)
    elif pattern == LayoutPattern.LIST_DETAIL:
        return manager.create_list_detail_layout(parent, **kwargs)
    elif pattern == LayoutPattern.DASHBOARD:
        return manager.create_dashboard_layout(parent, **kwargs)
    elif pattern == LayoutPattern.FORM:
        return manager.create_form_layout(parent, **kwargs)
    elif pattern == LayoutPattern.REPORT:
        return manager.create_report_layout(parent)
    else:
        raise ValueError(f"Unknown layout pattern: {pattern}")


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

layout_logger.info("=" * 70)
layout_logger.info("Layout Manager Module Loaded")
layout_logger.info(f"Available Patterns: {[p.value for p in LayoutPattern]}")
layout_logger.info("=" * 70)
