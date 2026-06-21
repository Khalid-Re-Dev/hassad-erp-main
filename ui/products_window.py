"""Product Management Window.

Provides CRUD operations for products and inventory items.

Phase F2.3 - Modernized with layout components and animations.
"""

from typing import Optional, Dict, Any
from decimal import Decimal

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QMessageBox, QDialog,
    QFormLayout, QComboBox, QCheckBox, QTextEdit,
    QDoubleSpinBox
)
from sqlalchemy.orm import Session

from core.database import SessionLocal
from ui.base_ui import ModuleMainWindow
from models.inventory import Product, Category, Unit
from models import Company
from core.services import get_product_service, ValidationError
from core.db_utils import session_scope
from ui.layout_components import Card, Toolbar, FilterBar, DataHeader, FormSection, Spacing
from ui.animations import fade_in, sequential_card_reveal, AnimationDuration
import logging
import uuid


class ProductDialog(QDialog):
    """Dialog for creating/editing products."""
    
    def __init__(self, product: Optional[Product] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.product = product
        self.is_edit = product is not None
        self._setup_ui()
        if self.is_edit:
            self._load_product_data()
    
    def _setup_ui(self) -> None:
        """Setup modern sectioned dialog UI."""
        self.setWindowTitle(
            "Edit Product | تعديل المنتج" if self.is_edit 
            else "Create Product | إنشاء منتج"
        )
        self.setMinimumWidth(750)
        self.setMinimumHeight(650)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(Spacing.MEDIUM.value)
        
        # Section 1: Basic Information
        basic_card = Card("Basic Information | المعلومات الأساسية", collapsible=True)
        basic_form = FormSection(columns=2)
        
        self.sku_input = QLineEdit()
        basic_form.add_field("SKU | رمز المنتج *", self.sku_input)
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Optional")
        basic_form.add_field("Barcode | الباركود", self.barcode_input)
        
        self.name_en_input = QLineEdit()
        basic_form.add_field("Name (English) | الاسم (إنجليزي) *", self.name_en_input)
        
        self.name_ar_input = QLineEdit()
        basic_form.add_field("Name (Arabic) | الاسم (عربي)", self.name_ar_input)
        
        basic_card.add_widget(basic_form)
        main_layout.addWidget(basic_card)
        
        # Section 2: Description
        desc_card = Card("Description | الوصف", collapsible=True)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Product description... | وصف المنتج...")
        desc_card.add_widget(self.description_input)
        main_layout.addWidget(desc_card)
        
        # Section 3: Classification
        class_card = Card("Classification | التصنيف", collapsible=True)
        class_form = FormSection(columns=2)
        
        self.category_combo = QComboBox()
        self._load_categories()
        class_form.add_field("Category | الفئة", self.category_combo)
        
        self.unit_combo = QComboBox()
        self._load_units()
        class_form.add_field("Base Unit | الوحدة الأساسية *", self.unit_combo)
        
        class_card.add_widget(class_form)
        main_layout.addWidget(class_card)
        
        # Section 4: Inventory Settings
        inv_card = Card("Inventory Settings | إعدادات المخزون")
        inv_layout = QVBoxLayout()
        inv_layout.setSpacing(Spacing.SMALL.value)
        
        self.track_batches_checkbox = QCheckBox("Track Batches | تتبع الدفعات")
        inv_layout.addWidget(self.track_batches_checkbox)
        
        self.track_expiry_checkbox = QCheckBox("Track Expiry | تتبع تاريخ الانتهاء")
        inv_layout.addWidget(self.track_expiry_checkbox)
        
        self.active_checkbox = QCheckBox("Active | نشط")
        self.active_checkbox.setChecked(True)
        inv_layout.addWidget(self.active_checkbox)
        
        inv_widget = QWidget()
        inv_widget.setLayout(inv_layout)
        inv_card.add_widget(inv_widget)
        main_layout.addWidget(inv_card)
        
        main_layout.addStretch()
        
        # Action Buttons
        self._create_action_buttons(main_layout)
        
        # Animate card reveal
        cards = [basic_card, desc_card, class_card, inv_card]
        QTimer.singleShot(50, lambda: sequential_card_reveal(cards, delay_between=50, animation_duration=150))
    
    def _create_action_buttons(self, layout):
        """Create action button row."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.SMALL.value)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel | إلغاء")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save | حفظ")
        save_btn.setProperty("primary", True)
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_categories(self) -> None:
        """Load categories into combo box."""
        db = SessionLocal()
        try:
            categories = db.query(Category).filter(Category.is_active == True).all()
            self.category_combo.addItem("-- No Category --", None)
            for category in categories:
                self.category_combo.addItem(category.name_en, category.id)
        finally:
            db.close()
    
    def _load_units(self) -> None:
        """Load units into combo box."""
        db = SessionLocal()
        try:
            units = db.query(Unit).filter(Unit.is_active == True).all()
            for unit in units:
                self.unit_combo.addItem(f"{unit.name} ({unit.symbol})", unit.id)
        finally:
            db.close()
    
    def _load_product_data(self) -> None:
        """Load existing product data into form."""
        if not self.product:
            return
        
        self.sku_input.setText(self.product.sku)
        self.barcode_input.setText(self.product.barcode or "")
        self.name_en_input.setText(self.product.name_en)
        self.name_ar_input.setText(self.product.name_ar or "")
        self.description_input.setPlainText(self.product.description or "")
        self.track_batches_checkbox.setChecked(self.product.track_batches)
        self.track_expiry_checkbox.setChecked(self.product.track_expiry)
        self.active_checkbox.setChecked(self.product.is_active)
        
        # Set category
        if self.product.category_id:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == self.product.category_id:
                    self.category_combo.setCurrentIndex(i)
                    break
        
        # Set unit
        if self.product.base_unit_id:
            for i in range(self.unit_combo.count()):
                if self.unit_combo.itemData(i) == self.product.base_unit_id:
                    self.unit_combo.setCurrentIndex(i)
                    break
    
    def get_product_data(self) -> dict:
        """Get product data from form."""
        return {
            "sku": self.sku_input.text().strip(),
            "barcode": self.barcode_input.text().strip() or None,
            "name_en": self.name_en_input.text().strip(),
            "name_ar": self.name_ar_input.text().strip() or None,
            "description": self.description_input.toPlainText().strip() or None,
            "category_id": self.category_combo.currentData(),
            "base_unit_id": self.unit_combo.currentData(),
            "track_batches": self.track_batches_checkbox.isChecked(),
            "track_expiry": self.track_expiry_checkbox.isChecked(),
            "is_active": self.active_checkbox.isChecked()
        }


class ProductsWindow(ModuleMainWindow):
    """Product management window."""
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        self._setup_ui()
        # Load data using the ModuleUI refresh_view method
        self.refresh_view()
    
    def _setup_ui(self) -> None:
        """Setup modern user interface with components."""
        self.setWindowTitle("Product Management | إدارة المنتجات")
        self.setMinimumSize(1200, 700)
        
        # Page Header
        header = DataHeader(
            title="Product Management | إدارة المنتجات",
            subtitle="0 products | 0 منتج"
        )
        self.main_layout.addWidget(header)
        
        # Main Content Card
        main_card = Card()
        
        # Toolbar
        toolbar = Toolbar()
        toolbar.add_action("Add Product | إضافة منتج", self._add_product, primary=True)
        toolbar.add_action("Edit | تعديل", self._edit_product)
        toolbar.add_action("Delete | حذف", self._delete_product, danger=True)
        toolbar.add_separator()
        toolbar.add_action("Export | تصدير", self._export_products)
        toolbar.add_spacer()
        toolbar.add_action("Refresh | تحديث", self.refresh_view)
        main_card.add_widget(toolbar)
        
        # Filter Bar
        filter_bar = FilterBar("Search products... | بحث عن المنتجات...")
        filter_bar.search_changed.connect(self._on_search)
        filter_bar.add_filter(
            "Category | الفئة",
            ["All | الكل", "Uncategorized | بدون فئة"],
            self._on_category_filter
        )
        filter_bar.add_filter(
            "Status | الحالة",
            ["All | الكل", "Active | نشط", "Inactive | غير نشط"],
            self._on_status_filter
        )
        main_card.add_widget(filter_bar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "SKU | رمز المنتج",
            "Barcode | الباركود",
            "Name | الاسم",
            "Category | الفئة",
            "Unit | الوحدة",
            "Batches | الدفعات",
            "Status | الحالة"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_product)
        main_card.add_widget(self.table)
        
        self.main_layout.addWidget(main_card)
        
        # Store references for updates
        self.header = header
        self.main_card = main_card
        self.filter_bar = filter_bar
        self.search_input = filter_bar.search_field  # Maintain compatibility
        self._category_filter = "All"
        self._status_filter = "All"
        
        # Apply fade-in animation
        QTimer.singleShot(50, lambda: fade_in(main_card, duration=AnimationDuration.NORMAL.value))
    
    def _on_search(self, text: str):
        """Handle search text changes."""
        self.refresh_view()
    
    def _on_category_filter(self, label: str, value: str):
        """Handle category filter changes."""
        self._category_filter = value
        self.refresh_view()
    
    def _on_status_filter(self, label: str, value: str):
        """Handle status filter changes."""
        self._status_filter = value
        self.refresh_view()
    
    def _export_products(self):
        """Export products to file."""
        self._show_info(
            "Export functionality coming soon. | وظيفة التصدير قريباً.",
            "Coming Soon | قريباً"
        )
    
    def load_data(self, session: Session) -> None:
        """Load products from database using provided session."""
        query = session.query(Product)
        
        # Apply search filter
        search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
        if search_term:
            query = query.filter(
                (Product.sku.ilike(f"%{search_term}%")) |
                (Product.barcode.ilike(f"%{search_term}%")) |
                (Product.name_en.ilike(f"%{search_term}%")) |
                (Product.name_ar.ilike(f"%{search_term}%"))
            )
        
        # Apply category filter
        if hasattr(self, '_category_filter') and "Uncategorized" in self._category_filter or "بدون فئة" in self._category_filter:
            query = query.filter(Product.category_id == None)
        
        # Apply status filter
        if hasattr(self, '_status_filter') and self._status_filter != "All" and "All" not in self._status_filter:
            if "Active" in self._status_filter or "نشط" in self._status_filter:
                query = query.filter(Product.is_active == True)
            elif "Inactive" in self._status_filter or "غير نشط" in self._status_filter:
                query = query.filter(Product.is_active == False)
        
        products = query.order_by(Product.sku).all()
        
        if hasattr(self, 'table'):
            self.table.setRowCount(len(products))
            for row, product in enumerate(products):
                self.table.setItem(row, 0, QTableWidgetItem(product.sku))
                self.table.setItem(row, 1, QTableWidgetItem(product.barcode or ""))
                self.table.setItem(row, 2, QTableWidgetItem(product.name_en))
                # Safely access related objects
                category_name = ""
                unit_symbol = ""
                try:
                    category_name = product.category.name_en if product.category else ""
                    unit_symbol = product.base_unit.symbol if product.base_unit else ""
                except:
                    pass
                self.table.setItem(row, 3, QTableWidgetItem(category_name))
                self.table.setItem(row, 4, QTableWidgetItem(unit_symbol))
                self.table.setItem(row, 5, QTableWidgetItem("Yes | نعم" if product.track_batches else "No | لا"))
                self.table.setItem(row, 6, QTableWidgetItem("Active | نشط" if product.is_active else "Inactive | غير نشط"))
                
                # Store product ID in first column
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, product.id)
            
            # Update header count
            if hasattr(self, 'header'):
                self.header.set_count(len(products), "products | منتجات")
    
    def _add_product(self) -> None:
        """Show dialog to add new product."""
        dialog = ProductDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_product_data()
            self._save_product(data)
    
    def _edit_product(self) -> None:
        """Edit selected product."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a product to edit.")
            return
        
        product_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        db = SessionLocal()
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                dialog = ProductDialog(product=product, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_product_data()
                    self._update_product(product_id, data)
        finally:
            db.close()
    
    def _delete_product(self) -> None:
        """Delete selected product via service layer."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a product to delete. | يرجى اختيار منتج للحذف.")
            return
        
        sku = self.table.item(current_row, 0).text()
        reply = QMessageBox.question(
            self,
            "Confirm Delete | تأكيد الحذف",
            f"Are you sure you want to delete product '{sku}'?\n\nهل أنت متأكد من حذف المنتج '{sku}'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            product_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            service = get_product_service()
            
            try:
                with session_scope() as session:
                    success, errors = service.delete(session, product_id)
                    
                    if not success or errors:
                        self._display_validation_errors(errors)
                        return
                    
                    QMessageBox.information(
                        self,
                        "Success | نجاح",
                        "Product deleted successfully.\n\nتم حذف المنتج بنجاح."
                    )
                    self.refresh_view()
            except Exception as e:
                error_id = str(uuid.uuid4())[:8]
                logger = logging.getLogger(__name__)
                logger.exception(f"Product deletion error {error_id}: {e}")
                QMessageBox.critical(
                    self,
                    "Error | خطأ",
                    f"Failed to delete product | فشل حذف المنتج\nError ID: {error_id}\nDetails: {str(e)}"
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
        QMessageBox.critical(self, "Validation | التحقق", message)
    
    def _save_product(self, data: dict) -> None:
        """Save new product via service layer."""
        service = get_product_service()
        
        # Add company_id from current user
        from core.session_manager import session_manager
        current_user = session_manager.get_active_user()
        if current_user:
            data['company_id'] = current_user.company_id
        
        try:
            with session_scope() as session:
                instance, errors = service.create(session, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                QMessageBox.information(
                    self,
                    "Success | نجاح",
                    "Product created successfully.\n\nتم إنشاء المنتج بنجاح."
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"Product creation error {error_id}: {e}")
            QMessageBox.critical(
                self,
                "Error | خطأ",
                f"Failed to create product | فشل إنشاء المنتج\nError ID: {error_id}\nDetails: {str(e)}"
            )
    
    def _update_product(self, product_id, data: dict) -> None:
        """Update existing product via service layer."""
        service = get_product_service()
        
        try:
            with session_scope() as session:
                instance, errors = service.update(session, product_id, data)
                
                if errors:
                    self._display_validation_errors(errors)
                    return
                
                QMessageBox.information(
                    self,
                    "Success | نجاح",
                    "Product updated successfully.\n\nتم تحديث المنتج بنجاح."
                )
                self.refresh_view()
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger = logging.getLogger(__name__)
            logger.exception(f"Product update error {error_id}: {e}")
            QMessageBox.critical(
                self,
                "Error | خطأ",
                f"Failed to update product | فشل تحديث المنتج\nError ID: {error_id}\nDetails: {str(e)}"
            )
