"""
Layout Templates for Hassad ERP
================================

Ready-to-use layout templates for common UI patterns.
These templates demonstrate best practices and can be used as starting points.

Templates:
- Modern CRUD Window Template
- List-Detail Window Template
- Dashboard Window Template
- Form Dialog Template
- Report Window Template

Phase: F2.2 - Layout System Architecture
Version: 1.0.0
"""

import logging
from typing import Optional, Dict, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QLabel,
    QDialog, QDialogButtonBox
)

from ui.layout_manager import LayoutManager, LayoutPattern
from ui.layout_components import Card, Toolbar, FilterBar, Spacing, DataHeader

# Configure logging
logger = logging.getLogger(__name__)
layout_logger = logging.getLogger('layout_engine')


# ============================================================================
# MODERN CRUD TEMPLATE
# ============================================================================

class ModernCRUDTemplate(QWidget):
    """
    Modern CRUD window template with:
    - Action toolbar
    - Search/filter bar
    - Data view (table or cards)
    - Consistent styling
    
    This is a template showing the pattern. Copy and customize for your module.
    """
    
    def __init__(self, title: str = "Data Management", parent: Optional[QWidget] = None):
        """
        Initialize CRUD template.
        
        Args:
            title: Window title
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.layout_manager = LayoutManager()
        
        self._setup_ui()
        layout_logger.info(f"ModernCRUDTemplate created: {title}")
    
    def _setup_ui(self):
        """Setup UI using layout manager."""
        # Create CRUD layout
        container, components = self.layout_manager.create_crud_layout(self)
        
        # Get components
        self.toolbar = components['toolbar']
        self.filter_bar = components['filter_bar']
        self.data_container = components['data_container']
        self.data_layout = components['data_layout']
        
        # Setup toolbar actions
        self.toolbar.add_action("Add | إضافة", self._on_add, primary=True)
        self.toolbar.add_action("Edit | تعديل", self._on_edit)
        self.toolbar.add_action("Delete | حذف", self._on_delete, danger=True)
        self.toolbar.add_separator()
        self.toolbar.add_action("Refresh | تحديث", self._on_refresh)
        self.toolbar.add_spacer()
        self.toolbar.add_action("Export | تصدير", self._on_export)
        
        # Setup filter bar
        self.filter_bar.search_changed.connect(self._on_search)
        status_filter = self.filter_bar.add_filter(
            "Status",
            ["All", "Active", "Inactive"],
            self._on_filter
        )
        
        # Add data view (table as example)
        self.table = QTableWidget()
        self.data_layout.addWidget(self.table)
        
        # Apply to main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
    
    # Action handlers (to be implemented by subclasses)
    def _on_add(self):
        """Handle add action."""
        logger.info(f"{self.title}: Add clicked")
    
    def _on_edit(self):
        """Handle edit action."""
        logger.info(f"{self.title}: Edit clicked")
    
    def _on_delete(self):
        """Handle delete action."""
        logger.info(f"{self.title}: Delete clicked")
    
    def _on_refresh(self):
        """Handle refresh action."""
        logger.info(f"{self.title}: Refresh clicked")
    
    def _on_export(self):
        """Handle export action."""
        logger.info(f"{self.title}: Export clicked")
    
    def _on_search(self, text: str):
        """Handle search."""
        logger.info(f"{self.title}: Search: {text}")
    
    def _on_filter(self, label: str, value: str):
        """Handle filter change."""
        logger.info(f"{self.title}: Filter {label}={value}")


# ============================================================================
# LIST-DETAIL TEMPLATE
# ============================================================================

class ListDetailTemplate(QWidget):
    """
    List-Detail window template with:
    - Left: Searchable list
    - Right: Detail view with edit capabilities
    """
    
    def __init__(self, title: str = "Items", parent: Optional[QWidget] = None):
        """
        Initialize list-detail template.
        
        Args:
            title: Window title
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.layout_manager = LayoutManager()
        
        self._setup_ui()
        layout_logger.info(f"ListDetailTemplate created: {title}")
    
    def _setup_ui(self):
        """Setup UI using layout manager."""
        # Create list-detail layout
        container, components = self.layout_manager.create_list_detail_layout(
            self,
            split_ratio=(0.35, 0.65)
        )
        
        # Get components
        self.list_filter = components['list_filter']
        self.list_container = components['list_container']
        self.detail_header = components['detail_header']
        self.detail_container = components['detail_container']
        
        # Setup list
        list_layout = components['list_container'].layout()
        self.list_widget = QTableWidget()
        list_layout.addWidget(self.list_widget)
        
        # Setup detail view
        detail_layout = components['detail_container'].layout()
        
        # Detail content in a card
        detail_card = Card("Details | التفاصيل")
        detail_content_layout = QVBoxLayout()
        
        # Add detail fields (example)
        detail_content_layout.addWidget(QLabel("Name:"))
        detail_content_layout.addWidget(QLabel("[Value]"))
        detail_content_layout.addWidget(QLabel("Description:"))
        detail_content_layout.addWidget(QLabel("[Value]"))
        detail_content_layout.addStretch()
        
        detail_card.body_layout.addLayout(detail_content_layout)
        
        # Add actions to detail card footer
        detail_card.set_footer_visible(True)
        save_btn = QPushButton("Save | حفظ")
        save_btn.setProperty("primary", True)
        detail_card.add_footer_widget(save_btn)
        
        cancel_btn = QPushButton("Cancel | إلغاء")
        detail_card.add_footer_widget(cancel_btn)
        
        detail_layout.addWidget(detail_card)
        
        # Apply to main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)


# ============================================================================
# DASHBOARD TEMPLATE
# ============================================================================

class DashboardTemplate(QWidget):
    """
    Dashboard template with:
    - Header with welcome message
    - Grid of KPI cards
    - Recent activity section
    """
    
    def __init__(self, user_name: str = "User", parent: Optional[QWidget] = None):
        """
        Initialize dashboard template.
        
        Args:
            user_name: Current user name
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.user_name = user_name
        self.layout_manager = LayoutManager()
        
        self._setup_ui()
        layout_logger.info("DashboardTemplate created")
    
    def _setup_ui(self):
        """Setup UI using layout manager."""
        # Create dashboard layout
        container, components = self.layout_manager.create_dashboard_layout(
            self,
            grid_columns=3
        )
        
        # Get components
        self.header = components['header']
        self.grid_layout = components['grid_layout']
        
        # Update header
        self.header.set_count(0, "")
        self.header.subtitle_label.setText(f"Welcome back, {self.user_name} | مرحباً بعودتك، {self.user_name}")
        
        # Add KPI cards to grid
        self._add_kpi_cards()
        
        # Apply to main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
    
    def _add_kpi_cards(self):
        """Add KPI cards to dashboard."""
        # Example KPI cards
        kpis = [
            ("Total Sales | إجمالي المبيعات", "$125,430", "success"),
            ("Active Orders | الطلبات النشطة", "47", "primary"),
            ("Pending Tasks | المهام المعلقة", "12", "warning"),
            ("Low Stock Items | منتجات منخفضة المخزون", "8", "danger"),
            ("New Customers | عملاء جدد", "23", "success"),
            ("Inventory Value | قيمة المخزون", "$89,200", "primary"),
        ]
        
        row, col = 0, 0
        for title, value, style in kpis:
            card = self._create_kpi_card(title, value, style)
            self.grid_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
    
    def _create_kpi_card(self, title: str, value: str, style: str) -> Card:
        """Create a KPI card."""
        card = Card()
        card.setMinimumHeight(120)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(Spacing.SMALL.value)
        
        title_label = QLabel(title)
        title_label.setProperty("subheading", True)
        content_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setProperty("heading", True)
        if style == "success":
            value_label.setProperty("success", True)
        elif style == "danger":
            value_label.setProperty("error", True)
        content_layout.addWidget(value_label)
        
        content_layout.addStretch()
        
        card.body_layout.addLayout(content_layout)
        
        return card


# ============================================================================
# FORM DIALOG TEMPLATE
# ============================================================================

class FormDialogTemplate(QDialog):
    """
    Form dialog template with:
    - Multi-section form
    - Standard buttons (OK, Cancel)
    - Validation support
    """
    
    def __init__(self, title: str = "Form", parent: Optional[QWidget] = None):
        """
        Initialize form dialog template.
        
        Args:
            title: Dialog title
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.layout_manager = LayoutManager()
        
        self._setup_ui()
        layout_logger.info(f"FormDialogTemplate created: {title}")
    
    def _setup_ui(self):
        """Setup UI using layout manager."""
        # Create form layout
        container, components = self.layout_manager.create_form_layout(
            self,
            sections=["Basic Information | معلومات أساسية", "Additional Details | تفاصيل إضافية"]
        )
        
        # Get components
        self.header = components['header']
        self.sections = components['sections']
        self.footer_layout = components['footer_layout']
        
        # Add standard dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.footer_layout.addWidget(button_box)
        
        # Apply to main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)


# ============================================================================
# REPORT TEMPLATE
# ============================================================================

class ReportTemplate(QWidget):
    """
    Report window template with:
    - Header with export actions
    - Collapsible filter panel
    - Report data view
    - Summary footer
    """
    
    def __init__(self, title: str = "Report", parent: Optional[QWidget] = None):
        """
        Initialize report template.
        
        Args:
            title: Report title
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.title = title
        self.layout_manager = LayoutManager()
        
        self._setup_ui()
        layout_logger.info(f"ReportTemplate created: {title}")
    
    def _setup_ui(self):
        """Setup UI using layout manager."""
        # Create report layout
        container, components = self.layout_manager.create_report_layout(self)
        
        # Get components
        self.header = components['header']
        self.filter_panel = components['filter_panel']
        self.report_layout = components['report_layout']
        self.summary_layout = components['summary_layout']
        
        # Setup header
        self.header.set_title(self.title)
        self.header.add_action("Export PDF | تصدير PDF", self._on_export_pdf)
        self.header.add_action("Export Excel | تصدير Excel", self._on_export_excel)
        self.header.add_action("Print | طباعة", self._on_print)
        
        # Add filter controls to panel
        # (Filters would be added here based on report type)
        
        # Add report table
        self.report_table = QTableWidget()
        self.report_layout.addWidget(self.report_table)
        
        # Add summary labels
        self.summary_layout.addStretch()
        total_label = QLabel("Total: $0.00")
        total_label.setProperty("heading", True)
        self.summary_layout.addWidget(total_label)
        
        # Apply to main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
    
    def _on_export_pdf(self):
        """Export to PDF."""
        logger.info(f"{self.title}: Export PDF")
    
    def _on_export_excel(self):
        """Export to Excel."""
        logger.info(f"{self.title}: Export Excel")
    
    def _on_print(self):
        """Print report."""
        logger.info(f"{self.title}: Print")


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

layout_logger.info("=" * 70)
layout_logger.info("Layout Templates Module Loaded")
layout_logger.info("Available Templates: ModernCRUDTemplate, ListDetailTemplate, DashboardTemplate, FormDialogTemplate, ReportTemplate")
layout_logger.info("=" * 70)
