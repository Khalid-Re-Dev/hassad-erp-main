"""
Product Categories Window.

Provides full CRUD management for product categories: create, edit, delete
(soft), search and view, wired to :class:`CategoryService` in the services
layer. Supports an optional parent category (hierarchy). All business logic
lives in the service; this module only handles presentation.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.db_utils import session_scope
from core.services import get_category_service, ValidationError
from models import Category
from ui.base_ui import ModuleWidget

logger = logging.getLogger(__name__)


class CategoryDialog(QDialog):
    """Dialog for creating/editing a product category."""

    def __init__(
        self,
        category: Optional[Category] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the dialog.

        Args:
            category: Existing category to edit, or None to create a new one.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.category = category
        self.is_edit = category is not None
        self._setup_ui()
        self._load_parent_options()
        if self.is_edit:
            self._load_category_data()

    def _setup_ui(self) -> None:
        """Build the form UI."""
        self.setWindowTitle(
            "Edit Category | تعديل الفئة"
            if self.is_edit
            else "Create Category | إنشاء فئة"
        )
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Name (English, required).
        self.name_en_input = QLineEdit()
        form.addRow("Name (English) | الاسم (إنجليزي) *", self.name_en_input)

        # Name (Arabic).
        self.name_ar_input = QLineEdit()
        form.addRow("Name (Arabic) | الاسم (عربي)", self.name_ar_input)

        # Parent category.
        self.parent_combo = QComboBox()
        form.addRow("Parent Category | الفئة الأم", self.parent_combo)

        # Description.
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Optional | اختياري")
        form.addRow("Description | الوصف", self.description_input)

        # Active.
        self.active_checkbox = QCheckBox("Active | نشط")
        self.active_checkbox.setChecked(True)
        form.addRow("", self.active_checkbox)

        layout.addLayout(form)

        # Action buttons.
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel | إلغاء")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save | حفظ")
        save_btn.setProperty("primary", True)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _load_parent_options(self) -> None:
        """Load available parent categories into the combo box."""
        self.parent_combo.addItem("-- No Parent | بدون أصل --", None)
        db = SessionLocal()
        try:
            query = db.query(Category).filter(Category.is_active == True)
            # A category cannot be its own parent.
            if self.is_edit and self.category is not None:
                query = query.filter(Category.id != self.category.id)
            for category in query.order_by(Category.name_en).all():
                self.parent_combo.addItem(category.name_en, category.id)
        finally:
            db.close()

    def _load_category_data(self) -> None:
        """Populate the form with the existing category's values."""
        if not self.category:
            return
        self.name_en_input.setText(self.category.name_en or "")
        self.name_ar_input.setText(self.category.name_ar or "")
        self.description_input.setPlainText(self.category.description or "")
        self.active_checkbox.setChecked(bool(self.category.is_active))
        if self.category.parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self.category.parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break

    def get_category_data(self) -> Dict[str, Any]:
        """Collect form values into a service-ready dictionary."""
        return {
            "name_en": self.name_en_input.text().strip(),
            "name_ar": self.name_ar_input.text().strip() or None,
            "parent_id": self.parent_combo.currentData(),
            "description": self.description_input.toPlainText().strip() or None,
            "is_active": self.active_checkbox.isChecked(),
        }


class CategoriesWindow(ModuleWidget):
    """Product categories management window with full CRUD."""

    def __init__(
        self,
        app_context: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize the window and load data."""
        super().__init__(app_context, parent)
        self.setWindowTitle("Product Categories | فئات المنتجات")
        self._setup_ui()
        self.refresh_view()

    def _setup_ui(self) -> None:
        """Build the window UI."""
        # Header.
        header_layout = QHBoxLayout()
        title_label = QLabel("Categories | الفئات")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search categories... | البحث في الفئات...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.refresh_view)
        header_layout.addWidget(self.search_input)

        add_btn = QPushButton("+ Add Category | + إضافة فئة")
        add_btn.clicked.connect(self._add_category)
        header_layout.addWidget(add_btn)

        self.main_layout.addLayout(header_layout)

        # Table.
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Name (EN) | الاسم",
            "Name (AR) | الاسم عربي",
            "Parent | الأصل",
            "Description | الوصف",
            "Status | الحالة",
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_category)
        self.main_layout.addWidget(self.table)

        # Action buttons.
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        edit_btn = QPushButton("Edit | تعديل")
        edit_btn.clicked.connect(self._edit_category)
        action_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete | حذف")
        delete_btn.clicked.connect(self._delete_category)
        action_layout.addWidget(delete_btn)

        view_btn = QPushButton("View | عرض")
        view_btn.clicked.connect(self._view_item)
        action_layout.addWidget(view_btn)

        self.main_layout.addLayout(action_layout)

    # ========================
    # Data loading
    # ========================

    def load_data(self, session: Session) -> None:
        """
        Load categories from the database into the table.

        Args:
            session: Database session provided by ``refresh_view``.
        """
        query = session.query(Category)

        search_term = (
            self.search_input.text().strip() if hasattr(self, "search_input") else ""
        )
        if search_term:
            pattern = f"%{search_term}%"
            query = query.filter(
                (Category.name_en.ilike(pattern)) | (Category.name_ar.ilike(pattern))
            )

        categories = query.order_by(Category.name_en).limit(500).all()

        if not hasattr(self, "table"):
            return

        # Build an id -> name map for resolving parent names cheaply.
        name_by_id = {c.id: c.name_en for c in categories}

        self.table.setRowCount(len(categories))
        for row, category in enumerate(categories):
            parent_name = ""
            if category.parent_id:
                parent_name = name_by_id.get(category.parent_id, "")
                if not parent_name:
                    try:
                        parent_name = category.parent.name_en if category.parent else ""
                    except Exception:  # noqa: BLE001
                        parent_name = ""
            self.table.setItem(row, 0, QTableWidgetItem(category.name_en or ""))
            self.table.setItem(row, 1, QTableWidgetItem(category.name_ar or ""))
            self.table.setItem(row, 2, QTableWidgetItem(parent_name))
            self.table.setItem(row, 3, QTableWidgetItem(category.description or ""))
            self.table.setItem(
                row,
                4,
                QTableWidgetItem(
                    "Active | نشط" if category.is_active else "Inactive | غير نشط"
                ),
            )
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, category.id)

    def _selected_category_id(self) -> Optional[Any]:
        """Return the id of the currently selected row, or None."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning(
                "Please select a category first. | يرجى اختيار فئة أولاً."
            )
            return None
        return self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

    # ========================
    # CREATE
    # ========================

    def _add_category(self) -> None:
        """Open the dialog to create a new category."""
        dialog = CategoryDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._save_category(dialog.get_category_data())

    def _save_category(self, data: Dict[str, Any]) -> None:
        """Persist a new category via the service layer."""
        service = get_category_service()

        company_id = self._resolve_company_id()
        if company_id is None:
            self._show_error("No active company found. | لا توجد شركة نشطة.")
            return
        data["company_id"] = company_id

        try:
            with session_scope() as session:
                instance, errors = service.create(session, data)
                if errors:
                    self._display_validation_errors(errors)
                    return
                self._show_info(
                    "Category created successfully.\n\nتم إنشاء الفئة بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("create", exc)

    # ========================
    # UPDATE
    # ========================

    def _edit_category(self) -> None:
        """Open the dialog to edit the selected category."""
        category_id = self._selected_category_id()
        if category_id is None:
            return

        db = SessionLocal()
        try:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                self._show_warning("Category not found. | الفئة غير موجودة.")
                return
            dialog = CategoryDialog(category=category, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._update_category(category_id, dialog.get_category_data())
        finally:
            db.close()

    def _update_category(self, category_id: Any, data: Dict[str, Any]) -> None:
        """Persist updates to an existing category via the service layer."""
        service = get_category_service()
        try:
            with session_scope() as session:
                instance, errors = service.update(session, category_id, data)
                if errors:
                    self._display_validation_errors(errors)
                    return
                self._show_info(
                    "Category updated successfully.\n\nتم تحديث الفئة بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("update", exc)

    # ========================
    # DELETE
    # ========================

    def _delete_category(self) -> None:
        """Soft-delete the selected category via the service layer."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning(
                "Please select a category to delete. | يرجى اختيار فئة للحذف."
            )
            return

        name = self.table.item(current_row, 0).text()
        if not self._ask_confirmation(
            f"Are you sure you want to delete category '{name}'?\n\n"
            f"هل أنت متأكد من حذف الفئة '{name}'؟",
            "Confirm Delete | تأكيد الحذف",
        ):
            return

        category_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        service = get_category_service()
        try:
            with session_scope() as session:
                success, errors = service.delete(session, category_id)
                if not success or errors:
                    self._display_validation_errors(errors)
                    return
                self._show_info(
                    "Category deleted successfully.\n\nتم حذف الفئة بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("delete", exc)

    # ========================
    # VIEW
    # ========================

    def _view_item(self) -> None:
        """Show a read-only summary of the selected category."""
        category_id = self._selected_category_id()
        if category_id is None:
            return

        db = SessionLocal()
        try:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                self._show_warning("Category not found. | الفئة غير موجودة.")
                return
            parent_name = "-"
            try:
                parent_name = category.parent.name_en if category.parent else "-"
            except Exception:  # noqa: BLE001
                parent_name = "-"
            details = (
                f"Name (EN) | الاسم: {category.name_en}\n"
                f"Name (AR) | الاسم (عربي): {category.name_ar or '-'}\n"
                f"Parent | الأصل: {parent_name}\n"
                f"Description | الوصف: {category.description or '-'}\n"
                f"Status | الحالة: "
                f"{'Active | نشط' if category.is_active else 'Inactive | غير نشط'}"
            )
            self._show_info(details, "Category Details | تفاصيل الفئة")
        finally:
            db.close()

    # ========================
    # Helpers
    # ========================

    def _resolve_company_id(self) -> Optional[Any]:
        """
        Resolve the company id for new records.

        Prefers the active user from the session manager (matching the
        products window pattern), falling back to the app context.
        """
        try:
            from core.session_manager import session_manager

            current_user = session_manager.get_active_user()
            if current_user and getattr(current_user, "company_id", None):
                return current_user.company_id
        except Exception:  # noqa: BLE001 - fall back to context below
            logger.debug("session_manager unavailable; falling back to app_context")

        current_company = self.app_context.get("current_company")
        if current_company is not None:
            return getattr(current_company, "id", None)

        current_user = self.app_context.get("current_user")
        if current_user is not None:
            return getattr(current_user, "company_id", None)
        return None

    def _display_validation_errors(self, errors: list) -> None:
        """Show bilingual validation errors to the user."""
        if not errors:
            return
        en_msgs = [f"- {e.get_message('en')} (field: {e.field})" for e in errors]
        ar_msgs = [f"- {e.get_message('ar')} (الحقل: {e.field})" for e in errors]
        message = (
            "Validation errors occurred:\n"
            + "\n".join(en_msgs)
            + "\n\nحدثت أخطاء في التحقق:\n"
            + "\n".join(ar_msgs)
        )
        self._show_error(message, title="Validation | التحقق")

    def _handle_unexpected_error(self, action: str, exc: Exception) -> None:
        """Log and surface an unexpected error with a trace id."""
        error_id = str(uuid.uuid4())[:8]
        logger.exception("Category %s error %s: %s", action, error_id, exc)
        self._show_error(
            f"Failed to {action} category | فشل {action} الفئة\n"
            f"Error ID: {error_id}\nDetails: {exc}",
            title="Error | خطأ",
        )
