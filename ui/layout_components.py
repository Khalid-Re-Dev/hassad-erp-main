"""
Layout Components Library for Hassad ERP
=========================================

Modern, reusable layout components for building consistent UIs.
Compatible with Theme Engine (F2.1) and RTL/LTR layouts.

Components:
- Card: Modern card container with header, body, footer
- Panel: Collapsible panel with sections
- Section: Logical grouping with optional header
- SplitView: Resizable split panel (horizontal/vertical)
- Toolbar: Action toolbar with consistent styling
- FormSection: Enhanced form container with grouping
- DataHeader: Header component for data views
- FilterBar: Search and filter bar component

Phase: F2.2 - Layout System Architecture
Version: 1.0.0
"""

import logging
from typing import Optional, List, Dict, Any
from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QToolButton, QSplitter, QScrollArea,
    QSizePolicy, QSpacerItem, QLineEdit, QComboBox
)
from PyQt6.QtGui import QIcon

# Configure logging
logger = logging.getLogger(__name__)

# Ensure logs directory exists
import os
os.makedirs('logs', exist_ok=True)

# Setup layout engine logger
layout_logger = logging.getLogger('layout_engine')
layout_logger.setLevel(logging.INFO)
layout_handler = logging.FileHandler('logs/layout_engine.log', encoding='utf-8')
layout_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
layout_handler.setFormatter(layout_formatter)
layout_logger.addHandler(layout_handler)


# ============================================================================
# LAYOUT CONSTANTS
# ============================================================================

class Spacing(Enum):
    """Standard spacing values (8px grid system)."""
    TINY = 4
    SMALL = 8
    MEDIUM = 16
    LARGE = 24
    XLARGE = 32


class CardStyle(Enum):
    """Card style variants."""
    DEFAULT = "default"
    PRIMARY = "primary"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


# ============================================================================
# CARD COMPONENT
# ============================================================================

class Card(QFrame):
    """
    Modern card container with header, body, and optional footer.
    
    Features:
    - Styled header with title
    - Scrollable body content
    - Optional footer for actions
    - Collapsible capability
    - Theme-aware styling
    - RTL compatible
    
    Signals:
        collapsed: Emitted when card is collapsed/expanded (bool)
    """
    
    collapsed = pyqtSignal(bool)
    
    def __init__(self, title: str = "", collapsible: bool = False, 
                 style: CardStyle = CardStyle.DEFAULT, parent: Optional[QWidget] = None):
        """
        Initialize card component.
        
        Args:
            title: Card title
            collapsible: Whether card can be collapsed
            style: Card visual style
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.collapsible = collapsible
        self.card_style = style
        self._is_collapsed = False
        
        self._setup_ui()
        layout_logger.info(f"Card created: title='{title}', collapsible={collapsible}")
    
    def _setup_ui(self):
        """Setup card UI structure."""
        # Card frame properties
        self.setObjectName("card")
        self.setProperty("card", True)
        self.setProperty("cardStyle", self.card_style.value)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header (if title provided)
        if self.title:
            self.header = self._create_header()
            main_layout.addWidget(self.header)
        
        # Body container
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(
            Spacing.MEDIUM.value, Spacing.MEDIUM.value,
            Spacing.MEDIUM.value, Spacing.MEDIUM.value
        )
        self.body_layout.setSpacing(Spacing.SMALL.value)
        
        main_layout.addWidget(self.body_container)
        
        # Footer (created on demand)
        self.footer = None
        self.footer_layout = None
    
    def _create_header(self) -> QWidget:
        """Create card header."""
        header = QWidget()
        header.setObjectName("cardHeader")
        header.setProperty("header", True)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(
            Spacing.MEDIUM.value, Spacing.SMALL.value,
            Spacing.MEDIUM.value, Spacing.SMALL.value
        )
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setProperty("heading", True)
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Collapse button
        if self.collapsible:
            self.collapse_btn = QToolButton()
            self.collapse_btn.setText("▼")
            self.collapse_btn.setProperty("icon", True)
            self.collapse_btn.clicked.connect(self.toggle_collapse)
            layout.addWidget(self.collapse_btn)
        
        return header
    
    def add_widget(self, widget: QWidget):
        """Add widget to card body."""
        self.body_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to card body."""
        self.body_layout.addLayout(layout)
    
    def set_footer_visible(self, visible: bool):
        """Show or hide footer."""
        if visible and not self.footer:
            self._create_footer()
        if self.footer:
            self.footer.setVisible(visible)
    
    def _create_footer(self):
        """Create card footer."""
        if self.footer:
            return
        
        self.footer = QWidget()
        self.footer.setObjectName("cardFooter")
        self.footer.setProperty("footer", True)
        
        self.footer_layout = QHBoxLayout(self.footer)
        self.footer_layout.setContentsMargins(
            Spacing.MEDIUM.value, Spacing.SMALL.value,
            Spacing.MEDIUM.value, Spacing.SMALL.value
        )
        
        self.layout().addWidget(self.footer)
    
    def add_footer_widget(self, widget: QWidget, align=Qt.AlignmentFlag.AlignRight):
        """Add widget to footer."""
        if not self.footer:
            self._create_footer()
        
        if align == Qt.AlignmentFlag.AlignLeft:
            self.footer_layout.insertWidget(0, widget)
        else:
            self.footer_layout.addWidget(widget)
    
    def toggle_collapse(self):
        """Toggle card collapse state."""
        self._is_collapsed = not self._is_collapsed
        self.body_container.setVisible(not self._is_collapsed)
        
        if hasattr(self, 'collapse_btn'):
            self.collapse_btn.setText("▶" if self._is_collapsed else "▼")
        
        self.collapsed.emit(self._is_collapsed)
        layout_logger.debug(f"Card '{self.title}' collapsed={self._is_collapsed}")
    
    def set_title(self, title: str):
        """Update card title."""
        self.title = title
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)


# ============================================================================
# PANEL COMPONENT
# ============================================================================

class Panel(QFrame):
    """
    Collapsible panel with header and content area.
    
    Lighter than Card, used for logical grouping.
    """
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, title: str = "", expanded: bool = True, parent: Optional[QWidget] = None):
        """
        Initialize panel.
        
        Args:
            title: Panel title
            expanded: Initial expanded state
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self._expanded = expanded
        
        self._setup_ui()
        layout_logger.info(f"Panel created: title='{title}', expanded={expanded}")
    
    def _setup_ui(self):
        """Setup panel UI."""
        self.setObjectName("panel")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header = QPushButton(self.title)
        self.header.setCheckable(True)
        self.header.setChecked(self._expanded)
        self.header.clicked.connect(self._on_header_clicked)
        layout.addWidget(self.header)
        
        # Content
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(
            Spacing.MEDIUM.value, Spacing.SMALL.value,
            Spacing.MEDIUM.value, Spacing.SMALL.value
        )
        self.content.setVisible(self._expanded)
        layout.addWidget(self.content)
    
    def _on_header_clicked(self):
        """Handle header click."""
        self._expanded = self.header.isChecked()
        self.content.setVisible(self._expanded)
        self.toggled.emit(self._expanded)
        layout_logger.debug(f"Panel '{self.title}' expanded={self._expanded}")
    
    def add_widget(self, widget: QWidget):
        """Add widget to panel content."""
        self.content_layout.addWidget(widget)
    
    def set_expanded(self, expanded: bool):
        """Set panel expanded state."""
        self._expanded = expanded
        self.header.setChecked(expanded)
        self.content.setVisible(expanded)


# ============================================================================
# SECTION COMPONENT
# ============================================================================

class Section(QWidget):
    """
    Logical grouping section with optional header.
    
    Lighter than Panel, no border, used for visual grouping.
    """
    
    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        """
        Initialize section.
        
        Args:
            title: Section title
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self._setup_ui()
        layout_logger.info(f"Section created: title='{title}'")
    
    def _setup_ui(self):
        """Setup section UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SMALL.value)
        
        if self.title:
            title_label = QLabel(self.title)
            title_label.setProperty("subheading", True)
            layout.addWidget(title_label)
        
        # Content container
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(Spacing.SMALL.value)
        layout.addWidget(self.content)
    
    def add_widget(self, widget: QWidget):
        """Add widget to section."""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to section."""
        self.content_layout.addLayout(layout)


# ============================================================================
# SPLIT VIEW COMPONENT
# ============================================================================

class SplitView(QSplitter):
    """
    Resizable split panel for list-detail or side-by-side layouts.
    
    Features:
    - Horizontal or vertical split
    - Resizable panels
    - Collapsible sides
    - Persistent sizes
    """
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent: Optional[QWidget] = None):
        """
        Initialize split view.
        
        Args:
            orientation: Qt.Horizontal or Qt.Vertical
            parent: Parent widget
        """
        super().__init__(orientation, parent)
        
        self.setChildrenCollapsible(False)
        self.setHandleWidth(2)
        
        layout_logger.info(f"SplitView created: orientation={'Horizontal' if orientation == Qt.Orientation.Horizontal else 'Vertical'}")
    
    def set_sizes_ratio(self, left_ratio: float, right_ratio: float):
        """
        Set panel sizes by ratio.
        
        Args:
            left_ratio: Ratio for left/top panel (0.0-1.0)
            right_ratio: Ratio for right/bottom panel (0.0-1.0)
        """
        total_size = self.width() if self.orientation() == Qt.Orientation.Horizontal else self.height()
        left_size = int(total_size * left_ratio)
        right_size = int(total_size * right_ratio)
        self.setSizes([left_size, right_size])


# ============================================================================
# TOOLBAR COMPONENT
# ============================================================================

class Toolbar(QWidget):
    """
    Action toolbar with consistent styling and button grouping.
    
    Features:
    - Primary and secondary action groups
    - Icon buttons
    - Spacers
    - Consistent styling
    """
    
    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        """
        Initialize toolbar.
        
        Args:
            title: Optional toolbar title
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self._setup_ui()
        layout_logger.info(f"Toolbar created: title='{title}'")
    
    def _setup_ui(self):
        """Setup toolbar UI."""
        self.setObjectName("toolbar")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(
            Spacing.MEDIUM.value, Spacing.SMALL.value,
            Spacing.MEDIUM.value, Spacing.SMALL.value
        )
        self.layout.setSpacing(Spacing.SMALL.value)
        
        if self.title:
            title_label = QLabel(self.title)
            title_label.setProperty("subheading", True)
            self.layout.addWidget(title_label)
            self.add_separator()
    
    def add_action(self, text: str, callback, icon: Optional[QIcon] = None, 
                   primary: bool = False, danger: bool = False) -> QPushButton:
        """
        Add action button to toolbar.
        
        Args:
            text: Button text
            callback: Click handler
            icon: Optional icon
            primary: Primary button style
            danger: Danger button style
            
        Returns:
            Created button
        """
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
        button.clicked.connect(callback)
        
        if primary:
            button.setProperty("primary", True)
        if danger:
            button.setProperty("danger", True)
        
        self.layout.addWidget(button)
        return button
    
    def add_separator(self):
        """Add visual separator."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)
    
    def add_spacer(self):
        """Add flexible spacer."""
        self.layout.addStretch()
    
    def add_widget(self, widget: QWidget):
        """Add custom widget to toolbar."""
        self.layout.addWidget(widget)


# ============================================================================
# FORM SECTION COMPONENT
# ============================================================================

class FormSection(QWidget):
    """
    Enhanced form container with logical grouping and multi-column support.
    
    Features:
    - Multi-column layouts
    - Section headers
    - Field grouping
    - Responsive columns
    """
    
    def __init__(self, title: str = "", columns: int = 1, parent: Optional[QWidget] = None):
        """
        Initialize form section.
        
        Args:
            title: Section title
            columns: Number of columns (1-3)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.columns = max(1, min(columns, 3))  # Clamp to 1-3
        
        self._setup_ui()
        layout_logger.info(f"FormSection created: title='{title}', columns={columns}")
    
    def _setup_ui(self):
        """Setup form section UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(Spacing.MEDIUM.value)
        
        if self.title:
            title_label = QLabel(self.title)
            title_label.setProperty("subheading", True)
            main_layout.addWidget(title_label)
        
        # Grid layout for form fields
        self.form_layout = QGridLayout()
        self.form_layout.setHorizontalSpacing(Spacing.MEDIUM.value)
        self.form_layout.setVerticalSpacing(Spacing.SMALL.value)
        main_layout.addLayout(self.form_layout)
        
        self._current_row = 0
        self._current_col = 0
    
    def add_field(self, label: str, widget: QWidget, span: int = 1):
        """
        Add field to form.
        
        Args:
            label: Field label
            widget: Input widget
            span: Column span (1-columns)
        """
        # Add label
        label_widget = QLabel(label)
        self.form_layout.addWidget(label_widget, self._current_row, self._current_col * 2)
        
        # Add widget
        col_span = min(span, self.columns) * 2 - 1
        self.form_layout.addWidget(widget, self._current_row, self._current_col * 2 + 1, 1, col_span)
        
        # Update position
        self._current_col += span
        if self._current_col >= self.columns:
            self._current_col = 0
            self._current_row += 1
    
    def add_row(self):
        """Start new row."""
        if self._current_col > 0:
            self._current_col = 0
            self._current_row += 1


# ============================================================================
# DATA HEADER COMPONENT
# ============================================================================

class DataHeader(QWidget):
    """
    Header component for data views with title, counts, and actions.
    """
    
    def __init__(self, title: str, subtitle: str = "", parent: Optional[QWidget] = None):
        """
        Initialize data header.
        
        Args:
            title: Main title
            subtitle: Optional subtitle
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.subtitle = subtitle
        
        self._setup_ui()
        layout_logger.info(f"DataHeader created: title='{title}'")
    
    def _setup_ui(self):
        """Setup header UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, Spacing.MEDIUM.value)
        
        # Title area
        title_layout = QVBoxLayout()
        
        self.title_label = QLabel(self.title)
        self.title_label.setProperty("heading", True)
        title_layout.addWidget(self.title_label)
        
        if self.subtitle:
            self.subtitle_label = QLabel(self.subtitle)
            self.subtitle_label.setProperty("info", True)
            title_layout.addWidget(self.subtitle_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Actions area (empty, to be filled)
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(Spacing.SMALL.value)
        layout.addLayout(self.actions_layout)
    
    def add_action(self, text: str, callback) -> QPushButton:
        """Add action button to header."""
        button = QPushButton(text)
        button.clicked.connect(callback)
        self.actions_layout.addWidget(button)
        return button
    
    def set_count(self, count: int, label: str = "items"):
        """Update subtitle with count."""
        self.subtitle = f"{count} {label}"
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.setText(self.subtitle)


# ============================================================================
# FILTER BAR COMPONENT
# ============================================================================

class FilterBar(QWidget):
    """
    Search and filter bar for data views.
    
    Features:
    - Search field
    - Quick filters
    - Clear all
    """
    
    search_changed = pyqtSignal(str)
    filter_changed = pyqtSignal(str, object)
    
    def __init__(self, placeholder: str = "Search... | بحث...", parent: Optional[QWidget] = None):
        """
        Initialize filter bar.
        
        Args:
            placeholder: Search field placeholder
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.placeholder = placeholder
        self._setup_ui()
        layout_logger.info("FilterBar created")
    
    def _setup_ui(self):
        """Setup filter bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, Spacing.SMALL.value)
        layout.setSpacing(Spacing.SMALL.value)
        
        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(self.placeholder)
        self.search_field.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_field, 1)
        
        # Filters container
        self.filters_layout = QHBoxLayout()
        self.filters_layout.setSpacing(Spacing.SMALL.value)
        layout.addLayout(self.filters_layout)
    
    def add_filter(self, label: str, options: List[str], callback) -> QComboBox:
        """
        Add filter dropdown.
        
        Args:
            label: Filter label
            options: Filter options
            callback: Selection handler
            
        Returns:
            Created combo box
        """
        filter_label = QLabel(label)
        self.filters_layout.addWidget(filter_label)
        
        combo = QComboBox()
        combo.addItems(options)
        combo.currentTextChanged.connect(lambda text: callback(label, text))
        combo.currentTextChanged.connect(lambda text: self.filter_changed.emit(label, text))
        self.filters_layout.addWidget(combo)
        
        return combo
    
    def clear(self):
        """Clear search and filters."""
        self.search_field.clear()


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

layout_logger.info("=" * 70)
layout_logger.info("Layout Components Library Loaded")
layout_logger.info("Available Components: Card, Panel, Section, SplitView, Toolbar, FormSection, DataHeader, FilterBar")
layout_logger.info("=" * 70)
