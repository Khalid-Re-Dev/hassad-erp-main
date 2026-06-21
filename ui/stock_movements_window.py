"""
Stock Movements Management Window.

Provides tracking and management of inventory stock movements and transactions.

TODO: Business Logic Implementation
- Stock movement recording (in, out, transfer)
- Movement type classification and validation  
- Real-time inventory level updates
- Movement history and audit trail
- Integration with sales, purchases, and adjustments
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
    QComboBox, QDateEdit
)

from ui.base_ui import ModuleWidget
from models.inventory import Product, StockMovement
from core.db_utils import session_scope
import uuid


class StockMovementsWindow(ModuleWidget):
    """
    Stock movements management window.
    
    Features:
    - Stock movement tracking
    - Movement type management
    - Inventory level monitoring
    - Movement history and reports
    
    TODO: Add comprehensive stock movement functionality
    """
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        self.setWindowTitle("Stock Movements | حركات المخزون")
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup user interface."""
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Stock Movements | حركات المخزون")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Filters
        self.movement_type_filter = QComboBox()
        self.movement_type_filter.addItems([
            "All Types | جميع الأنواع",
            "In | وارد", 
            "Out | صادر",
            "Transfer | نقل",
            "Adjustment | تسوية"
        ])
        self.movement_type_filter.currentTextChanged.connect(self.refresh_view)
        header_layout.addWidget(self.movement_type_filter)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products... | البحث في المنتجات...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.refresh_view)
        header_layout.addWidget(self.search_input)
        
        # Add movement button
        add_btn = QPushButton("+ Add Movement | + إضافة حركة")
        add_btn.clicked.connect(self._add_movement)
        header_layout.addWidget(add_btn)
        
        self.main_layout.addLayout(header_layout)
        
        # Table for movements display
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Date | التاريخ",
            "Product | المنتج", 
            "Type | النوع",
            "Quantity | الكمية",
            "Unit | الوحدة",
            "From | من",
            "To | إلى",
            "Reference | المرجع"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._view_movement)
        self.main_layout.addWidget(self.table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        view_btn = QPushButton("View Details | عرض التفاصيل")
        view_btn.clicked.connect(self._view_movement)
        action_layout.addWidget(view_btn)
        
        reverse_btn = QPushButton("Reverse Movement | عكس الحركة")
        reverse_btn.clicked.connect(self._reverse_movement)
        action_layout.addWidget(reverse_btn)
        
        self.main_layout.addLayout(action_layout)
        
    def load_data(self, session: Session) -> None:
        """
        Load stock movements from database.
        
        Args:
            session: Database session
        """
        try:
            # Query StockMovement model
            query = session.query(StockMovement)
            
            # Apply movement type filter
            movement_type = self.movement_type_filter.currentText() if hasattr(self, 'movement_type_filter') else ""
            if movement_type and not movement_type.startswith("All Types"):
                # Extract movement type from bilingual text (e.g., "In | وارد" -> "In")
                type_filter = movement_type.split(" | ")[0].strip()
                # TODO: Add actual filter when MovementType enum is available
                # query = query.filter(StockMovement.movement_type == type_filter)
            
            # Apply search filter
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
            if search_term and hasattr(StockMovement, 'reference'):
                query = query.filter(StockMovement.reference.ilike(f"%{search_term}%"))
            
            # Get results with proper joins for product info
            try:
                movements = query.order_by(StockMovement.movement_date.desc()).limit(100).all()
                
                if hasattr(self, 'table'):
                    self.table.setRowCount(len(movements))
                    for row, movement in enumerate(movements):
                        # Safely get attributes
                        date_str = movement.movement_date.strftime("%Y-%m-%d") if hasattr(movement, 'movement_date') and movement.movement_date else "N/A"
                        product_name = movement.product.name_en if hasattr(movement, 'product') and movement.product and hasattr(movement.product, 'name_en') else "Unknown Product"
                        movement_type = getattr(movement, 'movement_type', 'Unknown')
                        quantity = str(getattr(movement, 'quantity', '0'))
                        unit = movement.product.base_unit.symbol if hasattr(movement, 'product') and movement.product and hasattr(movement.product, 'base_unit') and movement.product.base_unit else "Unit"
                        from_location = getattr(movement, 'from_location', 'N/A')
                        to_location = getattr(movement, 'to_location', 'N/A')
                        reference = getattr(movement, 'reference', 'N/A')
                        
                        # Populate table
                        self.table.setItem(row, 0, QTableWidgetItem(date_str))
                        self.table.setItem(row, 1, QTableWidgetItem(product_name))
                        self.table.setItem(row, 2, QTableWidgetItem(str(movement_type)))
                        self.table.setItem(row, 3, QTableWidgetItem(quantity))
                        self.table.setItem(row, 4, QTableWidgetItem(unit))
                        self.table.setItem(row, 5, QTableWidgetItem(str(from_location)))
                        self.table.setItem(row, 6, QTableWidgetItem(str(to_location)))
                        self.table.setItem(row, 7, QTableWidgetItem(str(reference)))
                        
                        # Store movement ID for actions
                        if hasattr(movement, 'id'):
                            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, movement.id)
                            
            except Exception as db_error:
                # If StockMovement model doesn't have expected fields, show safe placeholder
                self._show_placeholder_data_with_notice(str(db_error))
                
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            error_msg = f"Failed to load stock movements data | فشل تحميل بيانات حركات المخزون\nError ID: {error_id}\nDetails: {str(e)}"
            self._show_error(error_msg)
            # Log the full error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Stock movements load error {error_id}: {e}")
            raise
    
    def _show_placeholder_data_with_notice(self, db_error: str):
        """Show placeholder data when database model is not fully available."""
        if hasattr(self, 'table'):
            # Show sample data with a notice that this is placeholder
            sample_data = [
                ("2025-01-15", "Product A (Sample)", "In | وارد", "100", "PCS", "Supplier", "Warehouse", "PO-001"),
                ("2025-01-16", "Product B (Sample)", "Out | صادر", "50", "KG", "Warehouse", "Customer", "SO-002"),
                ("2025-01-17", "Product C (Sample)", "Transfer | نقل", "25", "PCS", "Warehouse A", "Warehouse B", "TRF-003")
            ]
            
            self.table.setRowCount(len(sample_data))
            for row, data in enumerate(sample_data):
                for col, value in enumerate(data):
                    self.table.setItem(row, col, QTableWidgetItem(str(value)))
            
            # Log the database issue
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Stock movements using placeholder data due to DB model issue: {db_error}")
    
    def _add_movement(self):
        """Add new stock movement."""
        self._show_info(
            "Add Stock Movement functionality not yet implemented.\\n"
            "This will open a dialog to record a new stock movement.\\n\\n"
            "وظيفة إضافة حركة مخزون لم يتم تنفيذها بعد.\\n"
            "ستفتح نافذة حوار لتسجيل حركة مخزون جديدة.",
            "Coming Soon | قريباً"
        )
    
    def _view_movement(self):
        """View movement details."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning("Please select a movement to view. | يرجى اختيار حركة للعرض.")
            return
            
        self._show_info(
            "View Movement Details functionality not yet implemented.\\n"
            "This will show detailed information about the selected movement.\\n\\n"
            "وظيفة عرض تفاصيل الحركة لم يتم تنفيذها بعد.\\n"
            "ستعرض معلومات مفصلة عن الحركة المحددة.",
            "Coming Soon | قريباً"
        )
    
    def _display_validation_errors(self, errors: list) -> None:
        """Show bilingual validation errors to the user."""
        if not errors:
            return
        en_msgs = [f"- {e.get_message('en')} (field: {e.field})" for e in errors]
        ar_msgs = [f"- {e.get_message('ar')} (الحقل: {e.field})" for e in errors]
        message = (
            "Validation errors occurred:\n" + "\n".join(en_msgs) +
            "\n\nحدثت أخطاء في التحقق:\n" + "\n".join(ar_msgs)
        )
        self._show_error(message, title="Validation | التحقق")

    def _reverse_movement(self):
        """Reverse selected movement."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning("Please select a movement to reverse. | يرجى اختيار حركة لعكسها.")
            return
            
        if self._ask_confirmation(
            "Are you sure you want to reverse this stock movement?\\n"
            "This will create a compensating movement.\\n\\n"
            "هل أنت متأكد من عكس هذه الحركة؟\\n"
            "ستنشئ حركة تعويضية."
        ):
            self._show_info(
                "Reverse Movement functionality not yet implemented.\\n"
                "This will create a reverse movement to undo the selected transaction.\\n\\n"
                "وظيفة عكس الحركة لم يتم تنفيذها بعد.\\n"
                "ستنشئ حركة عكسية لإلغاء المعاملة المحددة.",
                "Coming Soon | قريباً"
            )