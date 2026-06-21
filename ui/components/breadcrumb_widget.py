"""
Breadcrumb Navigation Widget

Provides visual navigation context and quick navigation between sections.
Part of Phase F2.4 - User Flow & Navigation Enhancement.
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel
)


class BreadcrumbItem:
    """Represents a single breadcrumb item."""
    
    def __init__(self, id: str, name: str, name_ar: str, icon: str = ""):
        self.id = id
        self.name = name
        self.name_ar = name_ar
        self.icon = icon
    
    def get_display_name(self, show_arabic: bool = False) -> str:
        """Get display name based on language preference."""
        if show_arabic:
            return f"{self.name} | {self.name_ar}"
        return self.name


class BreadcrumbWidget(QWidget):
    """
    Breadcrumb navigation widget showing current location in the application.
    
    Features:
    - Hierarchical path display (Home > Setup > Company)
    - Clickable navigation to parent sections
    - Bilingual support (English/Arabic)
    - Icon display
    - Theme-aware styling
    
    Signals:
        breadcrumb_clicked(str): Emitted when a breadcrumb item is clicked
    """
    
    breadcrumb_clicked = pyqtSignal(str)
    
    def __init__(self, show_arabic: bool = False, separator: str = "›", parent: Optional[QWidget] = None):
        """
        Initialize breadcrumb widget.
        
        Args:
            show_arabic: Whether to show Arabic translations
            separator: Character to use between breadcrumb items
            parent: Parent widget
        """
        super().__init__(parent)
        self.show_arabic = show_arabic
        self.separator = separator
        self.breadcrumb_items: List[BreadcrumbItem] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup user interface."""
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)
        
        # Set object name for styling
        self.setObjectName("breadcrumbWidget")
        
        # Initial home breadcrumb
        self._add_home_breadcrumb()
    
    def _add_home_breadcrumb(self):
        """Add home breadcrumb item."""
        home_item = BreadcrumbItem(
            id="dashboard",
            name="Home",
            name_ar="الرئيسية",
            icon="🏠"
        )
        self.breadcrumb_items = [home_item]
        self._render_breadcrumbs()
    
    def set_path(self, group_name: str = None, group_name_ar: str = None, 
                 module_id: str = None, module_name: str = None, module_name_ar: str = None,
                 module_icon: str = ""):
        """
        Set the breadcrumb path.
        
        Args:
            group_name: Name of the group (e.g., "Setup & Configuration")
            group_name_ar: Arabic name of the group
            module_id: Module identifier
            module_name: Name of the module (e.g., "Company Profile")
            module_name_ar: Arabic name of the module
            module_icon: Icon for the module
        """
        # Start with home
        self.breadcrumb_items = [BreadcrumbItem(
            id="dashboard",
            name="Home",
            name_ar="الرئيسية",
            icon="🏠"
        )]
        
        # Add group if provided
        if group_name and group_name_ar:
            group_item = BreadcrumbItem(
                id=f"group_{group_name.lower().replace(' ', '_')}",
                name=group_name,
                name_ar=group_name_ar,
                icon=""
            )
            self.breadcrumb_items.append(group_item)
        
        # Add module if provided
        if module_id and module_name and module_name_ar:
            module_item = BreadcrumbItem(
                id=module_id,
                name=module_name,
                name_ar=module_name_ar,
                icon=module_icon
            )
            self.breadcrumb_items.append(module_item)
        
        self._render_breadcrumbs()
    
    def _render_breadcrumbs(self):
        """Render breadcrumb items in the layout."""
        # Clear existing widgets
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Render each breadcrumb item
        for index, item in enumerate(self.breadcrumb_items):
            # Add separator (except before first item)
            if index > 0:
                separator_label = QLabel(self.separator)
                separator_label.setStyleSheet("color: #95a5a6; font-size: 14px; padding: 0 5px;")
                self.layout.addWidget(separator_label)
            
            # Create breadcrumb button
            is_last = (index == len(self.breadcrumb_items) - 1)
            btn = self._create_breadcrumb_button(item, is_last)
            self.layout.addWidget(btn)
        
        # Add stretch to push items to the left
        self.layout.addStretch()
    
    def _create_breadcrumb_button(self, item: BreadcrumbItem, is_last: bool) -> QPushButton:
        """
        Create a breadcrumb button.
        
        Args:
            item: Breadcrumb item
            is_last: Whether this is the last (current) item
            
        Returns:
            QPushButton configured as breadcrumb
        """
        display_text = item.get_display_name(self.show_arabic)
        if item.icon:
            display_text = f"{item.icon} {display_text}"
        
        btn = QPushButton(display_text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFlat(True)
        
        # Style based on whether it's the current page
        if is_last:
            # Current page - not clickable, bold
            btn.setEnabled(False)
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    color: #2c3e50;
                    font-weight: bold;
                    font-size: 13px;
                    padding: 5px 10px;
                    text-align: left;
                }
            """)
        else:
            # Parent pages - clickable, blue
            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    color: #3498db;
                    font-size: 13px;
                    padding: 5px 10px;
                    text-align: left;
                }
                QPushButton:hover {
                    color: #2980b9;
                    text-decoration: underline;
                }
                QPushButton:pressed {
                    color: #21618c;
                }
            """)
            btn.clicked.connect(lambda checked, item_id=item.id: self.breadcrumb_clicked.emit(item_id))
        
        return btn
    
    def reset_to_home(self):
        """Reset breadcrumb to home only."""
        self._add_home_breadcrumb()
    
    def set_bilingual(self, show_arabic: bool):
        """
        Set bilingual display mode.
        
        Args:
            show_arabic: Whether to show Arabic translations
        """
        self.show_arabic = show_arabic
        self._render_breadcrumbs()
