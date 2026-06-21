"""
Hierarchical Navigation Widget

Provides organized, collapsible navigation following accounting workflow logic.
Part of Phase F2.4 - User Flow & Navigation Enhancement.
"""

import json
import os
from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame
)


class NavigationModule:
    """Represents a single navigation module."""
    
    def __init__(self, data: Dict):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.name_ar = data.get("name_ar", "")
        self.icon = data.get("icon", "")
        self.module_path = data.get("module_path", "")
        self.class_name = data.get("class_name", "")
        self.permission = data.get("permission", "")
        self.order = data.get("order", 0)
        self.tooltip = data.get("tooltip", "")
        self.workflow_step = data.get("workflow_step", 0)
        self.depends_on = data.get("depends_on", [])


class NavigationGroup:
    """Represents a collapsible navigation group."""
    
    def __init__(self, data: Dict):
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.name_ar = data.get("name_ar", "")
        self.icon = data.get("icon", "")
        self.order = data.get("order", 0)
        self.color = data.get("color", "#3498db")
        self.description = data.get("description", "")
        self.collapsible = data.get("collapsible", True)
        self.default_collapsed = data.get("default_collapsed", False)
        self.modules: List[NavigationModule] = [
            NavigationModule(mod) for mod in data.get("modules", [])
        ]


class NavigationGroupWidget(QWidget):
    """Widget representing a collapsible navigation group."""
    
    module_clicked = pyqtSignal(str, str, str, str, str)  # module_id, group_name, group_name_ar, module_name, module_name_ar
    
    def __init__(self, group: NavigationGroup, show_arabic: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.group = group
        self.show_arabic = show_arabic
        self.is_collapsed = group.default_collapsed
        self.module_widgets: List[QWidget] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup user interface for the group."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        # Group header button
        self.header_btn = self._create_header_button()
        layout.addWidget(self.header_btn)
        
        # Container for module items
        self.modules_container = QWidget()
        self.modules_container.setObjectName("modulesContainer")
        modules_layout = QVBoxLayout()
        modules_layout.setContentsMargins(0, 0, 0, 0)
        modules_layout.setSpacing(0)
        self.modules_container.setLayout(modules_layout)
        
        # Add module buttons
        for module in self.group.modules:
            module_btn = self._create_module_button(module)
            self.module_widgets.append(module_btn)
            modules_layout.addWidget(module_btn)
        
        layout.addWidget(self.modules_container)
        
        # Set initial collapsed state
        if self.is_collapsed:
            self.modules_container.hide()
    
    def _create_header_button(self) -> QPushButton:
        """Create the group header button."""
        display_name = self.group.name
        if self.show_arabic:
            display_name = f"{self.group.name} | {self.group.name_ar}"
        
        collapse_icon = "▼" if not self.is_collapsed else "▶"
        text = f"{collapse_icon} {self.group.icon} {display_name}"
        
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFlat(True)
        btn.clicked.connect(self._toggle_collapse)
        
        # Style the header
        btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background-color: {self.group.color};
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 15px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(self.group.color)};
            }}
        """)
        
        return btn
    
    def _create_module_button(self, module: NavigationModule) -> QPushButton:
        """Create a module navigation button."""
        display_name = module.name
        if self.show_arabic:
            display_name = f"{module.name} | {module.name_ar}"
        
        text = f"  {module.icon} {display_name}"
        
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFlat(True)
        btn.setToolTip(module.tooltip)
        
        # Store module data as property
        btn.setProperty("module_id", module.id)
        btn.setProperty("module_name", module.name)
        btn.setProperty("module_name_ar", module.name_ar)
        
        btn.clicked.connect(lambda: self.module_clicked.emit(
            module.id, 
            self.group.name, 
            self.group.name_ar,
            module.name,
            module.name_ar
        ))
        
        # Style the module button
        btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #ecf0f1;
                font-size: 13px;
                padding: 10px 15px 10px 30px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.3);
                border-left: 3px solid #3498db;
            }
            QPushButton:pressed {
                background-color: rgba(41, 128, 185, 0.5);
            }
        """)
        
        return btn
    
    def _toggle_collapse(self):
        """Toggle the collapsed state of the group."""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.modules_container.hide()
            collapse_icon = "▶"
        else:
            self.modules_container.show()
            collapse_icon = "▼"
        
        # Update header text
        display_name = self.group.name
        if self.show_arabic:
            display_name = f"{self.group.name} | {self.group.name_ar}"
        
        self.header_btn.setText(f"{collapse_icon} {self.group.icon} {display_name}")
    
    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color."""
        # Simple darkening - multiply RGB values by factor
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color
    
    def highlight_module(self, module_id: str):
        """Highlight a specific module in this group."""
        for widget in self.module_widgets:
            if isinstance(widget, QPushButton):
                if widget.property("module_id") == module_id:
                    widget.setStyleSheet("""
                        QPushButton {
                            border: none;
                            background-color: #3498db;
                            color: white;
                            font-size: 13px;
                            font-weight: bold;
                            padding: 10px 15px 10px 30px;
                            text-align: left;
                            border-left: 3px solid #2980b9;
                        }
                    """)
                else:
                    # Reset to normal
                    widget.setStyleSheet("""
                        QPushButton {
                            border: none;
                            background-color: transparent;
                            color: #ecf0f1;
                            font-size: 13px;
                            padding: 10px 15px 10px 30px;
                            text-align: left;
                        }
                        QPushButton:hover {
                            background-color: rgba(52, 152, 219, 0.3);
                            border-left: 3px solid #3498db;
                        }
                    """)


class NavigationWidget(QWidget):
    """
    Hierarchical navigation widget with collapsible groups.
    
    Features:
    - Loads navigation from navigation.json
    - Organizes modules into logical groups
    - Follows accounting workflow order
    - Collapsible sections
    - Bilingual support
    - Permission-aware (hides unauthorized modules)
    
    Signals:
        module_selected(module_id, group_name, group_name_ar, module_name, module_name_ar): 
            Emitted when a module is selected
    """
    
    module_selected = pyqtSignal(str, str, str, str, str)
    
    def __init__(self, user, permission_manager, show_arabic: bool = False, parent: Optional[QWidget] = None):
        """
        Initialize navigation widget.
        
        Args:
            user: Current user (for permission checking)
            permission_manager: Permission manager instance
            show_arabic: Whether to show Arabic translations
            parent: Parent widget
        """
        super().__init__(parent)
        self.user = user
        self.permission_manager = permission_manager
        self.show_arabic = show_arabic
        self.navigation_groups: List[NavigationGroup] = []
        self.group_widgets: List[NavigationGroupWidget] = []
        self.current_module_id: Optional[str] = None
        
        self._load_navigation_config()
        self._setup_ui()
    
    def _load_navigation_config(self):
        """Load navigation configuration from navigation.json."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "navigation.json")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Load navigation groups
            for group_data in config.get("navigation_groups", []):
                group = NavigationGroup(group_data)
                # Filter modules based on permissions
                group.modules = [
                    mod for mod in group.modules 
                    if self._has_permission(mod.permission)
                ]
                # Only add group if it has visible modules
                if group.modules:
                    self.navigation_groups.append(group)
            
            # Sort groups by order
            self.navigation_groups.sort(key=lambda g: g.order)
            
        except FileNotFoundError:
            print(f"Warning: navigation.json not found at {config_path}")
        except json.JSONDecodeError as e:
            print(f"Error parsing navigation.json: {e}")
    
    def _has_permission(self, permission: str) -> bool:
        """Check if user has required permission."""
        if not permission:
            return True
        return (self.permission_manager.has_permission(self.user, permission) or 
                self.permission_manager.is_admin(self.user))
    
    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        # Create scroll area for navigation
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container for groups
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)
        container.setLayout(container_layout)
        
        # Add navigation groups
        for group in self.navigation_groups:
            group_widget = NavigationGroupWidget(group, self.show_arabic, self)
            group_widget.module_clicked.connect(self._on_module_clicked)
            self.group_widgets.append(group_widget)
            container_layout.addWidget(group_widget)
        
        # Add stretch at the end
        container_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _on_module_clicked(self, module_id: str, group_name: str, group_name_ar: str, 
                          module_name: str, module_name_ar: str):
        """Handle module click event."""
        self.current_module_id = module_id
        
        # Highlight the selected module
        for group_widget in self.group_widgets:
            group_widget.highlight_module(module_id)
        
        # Emit signal
        self.module_selected.emit(module_id, group_name, group_name_ar, module_name, module_name_ar)
    
    def select_module(self, module_id: str):
        """
        Programmatically select a module.
        
        Args:
            module_id: ID of the module to select
        """
        self.current_module_id = module_id
        for group_widget in self.group_widgets:
            group_widget.highlight_module(module_id)
    
    def set_bilingual(self, show_arabic: bool):
        """
        Set bilingual display mode.
        
        Args:
            show_arabic: Whether to show Arabic translations
        """
        self.show_arabic = show_arabic
        # Rebuild UI with new language setting
        # Clear existing widgets
        for group_widget in self.group_widgets:
            group_widget.deleteLater()
        self.group_widgets.clear()
        
        # Recreate UI
        self._setup_ui()
