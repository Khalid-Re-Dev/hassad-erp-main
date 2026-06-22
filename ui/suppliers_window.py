"""
Suppliers Window.

Provides full CRUD management for suppliers (vendors): create, edit, delete
(soft), search and view, wired to :class:`SupplierService` in the services
layer. All business logic lives in the service; this module only handles
presentation and user interaction.
"""

import logging
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.db_utils import session_scope
from core.services import get_supplier_service, ValidationError
from models import Supplier
from ui.base_ui import ModuleWidget

logger = logging.getLogger(__name__)


class SupplierDialog(QDialog):
    """Dialog for creating/editing a supplier."""

    def __init__(
        self,
        supplier: Optional[Supplier] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the dialog.

        Args:
            supplier: Existing supplier to edit, or None to create a new one.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.supplier = supplier
        self.is_edit = supplier is not None
        self._setup_ui()
        if self.is_edit:
            self._load_supplier_data()

    def _setup_ui(self) -> None:
        """Build the form UI."""
        self.setWindowTitle(
            "Edit Supplier | تعديل المورد"
            if self.is_edit
            else "Create Supplier | إنشاء مورد"
        )
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Name (required).
        self.name_input = QLineEdit()
        form.addRow("Name | الاسم *", self.name_input)

        # Contact name.
        self.contact_name_input = QLineEdit()
        self.contact_name_input.setPlaceholderText("Optional | اختياري")
        form.addRow("Contact Name | جهة الاتصال", self.contact_name_input)

        # Phone.
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Optional | اختياري")
        form.addRow("Phone | الهاتف", self.phone_input)

        # Email.
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Optional | اختياري")
        form.addRow("Email | البريد الإلكتروني", self.email_input)

        # Tax id.
        self.tax_id_input = QLineEdit()
        self.tax_id_input.setPlaceholderText("Optional | اختياري")
        form.addRow("Tax ID | الرقم الضريبي", self.tax_id_input)

        # Address.
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        self.address_input.setPlaceholderText("Optional | اختياري")
        form.addRow("Address | العنوان", self.address_input)

        # Payment terms (days).
        self.payment_terms_input = QSpinBox()
        self.payment_terms_input.setMaximum(3650)
        self.payment_terms_input.setValue(30)
        self.payment_terms_input.setSuffix(" days | يوم")
        form.addRow("Payment Terms | شروط الدفع", self.payment_terms_input)

        # Preferred currency.
        self.currency_input = QLineEdit()
        self.currency_input.setText("SAR")
        self.currency_input.setMaxLength(3)
        form.addRow("Currency | العملة", self.currency_input)

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

    def _load_supplier_data(self) -> None:
        """Populate the form with the existing supplier's values."""
        if not self.supplier:
            return
        self.name_input.setText(self.supplier.name or "")
        self.contact_name_input.setText(self.supplier.contact_name or "")
        self.phone_input.setText(self.supplier.phone or "")
        self.email_input.setText(self.supplier.email or "")
        self.tax_id_input.setText(self.supplier.tax_id or "")
        self.address_input.setPlainText(self.supplier.address or "")
        if self.supplier.default_payment_terms is not None:
            self.payment_terms_input.setValue(int(self.supplier.default_payment_terms))
        self.currency_input.setText(self.supplier.preferred_currency or "SAR")
        self.active_checkbox.setChecked(bool(self.supplier.is_active))

    def get_supplier_data(self) -> Dict[str, Any]:
        """Collect form values into a service-ready dictionary."""
        return {
            "name": self.name_input.text().strip(),
            "contact_name": self.contact_name_input.text().strip() or None,
            "phone": self.phone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "tax_id": self.tax_id_input.text().strip() or None,
            "address": self.address_input.toPlainText().strip() or None,
            "default_payment_terms": Decimal(str(self.payment_terms_input.value())),
            "preferred_currency": self.currency_input.text().strip().upper() or None,
            "is_active": self.active_checkbox.isChecked(),
        }


class SuppliersWindow(ModuleWidget):
    """Suppliers management window with full CRUD."""

    def __init__(
        self,
        app_context: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize the window and load data."""
        super().__init__(app_context, parent)
        self.setWindowTitle("Suppliers | الموردين")
        self._setup_ui()
        self.refresh_view()

    def _setup_ui(self) -> None:
        """Build the window UI."""
        # Header.
        header_layout = QHBoxLayout()
        title_label = QLabel("Suppliers | الموردين")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search suppliers... | البحث في الموردين...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.refresh_view)
        header_layout.addWidget(self.search_input)

        add_btn = QPushButton("+ Add Supplier | + إضافة مورد")
        add_btn.clicked.connect(self._add_supplier)
        header_layout.addWidget(add_btn)

        self.main_layout.addLayout(header_layout)

        # Table.
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name | الاسم",
            "Contact | جهة الاتصال",
            "Phone | الهاتف",
            "Email | البريد",
            "Payment Terms | شروط الدفع",
            "Status | الحالة",
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_supplier)
        self.main_layout.addWidget(self.table)

        # Action buttons.
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        edit_btn = QPushButton("Edit | تعديل")
        edit_btn.clicked.connect(self._edit_supplier)
        action_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete | حذف")
        delete_btn.clicked.connect(self._delete_supplier)
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
        Load suppliers from the database into the table.

        Args:
            session: Database session provided by ``refresh_view``.
        """
        query = session.query(Supplier)

        search_term = (
            self.search_input.text().strip() if hasattr(self, "search_input") else ""
        )
        if search_term:
            pattern = f"%{search_term}%"
            query = query.filter(
                (Supplier.name.ilike(pattern))
                | (Supplier.contact_name.ilike(pattern))
                | (Supplier.phone.ilike(pattern))
                | (Supplier.email.ilike(pattern))
                | (Supplier.tax_id.ilike(pattern))
            )

        suppliers = query.order_by(Supplier.name).limit(500).all()

        if not hasattr(self, "table"):
            return

        self.table.setRowCount(len(suppliers))
        for row, supplier in enumerate(suppliers):
            terms = (
                f"{int(supplier.default_payment_terms)} days | يوم"
                if supplier.default_payment_terms is not None
                else ""
            )
            self.table.setItem(row, 0, QTableWidgetItem(supplier.name or ""))
            self.table.setItem(row, 1, QTableWidgetItem(supplier.contact_name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(supplier.phone or ""))
            self.table.setItem(row, 3, QTableWidgetItem(supplier.email or ""))
            self.table.setItem(row, 4, QTableWidgetItem(terms))
            self.table.setItem(
                row,
                5,
                QTableWidgetItem(
                    "Active | نشط" if supplier.is_active else "Inactive | غير نشط"
                ),
            )
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, supplier.id)

    def _selected_supplier_id(self) -> Optional[Any]:
        """Return the id of the currently selected row, or None."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning(
                "Please select a supplier first. | يرجى اختيار مورد أولاً."
            )
            return None
        return self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

    # ========================
    # CREATE
    # ========================

    def _add_supplier(self) -> None:
        """Open the dialog to create a new supplier."""
        dialog = SupplierDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._save_supplier(dialog.get_supplier_data())

    def _save_supplier(self, data: Dict[str, Any]) -> None:
        """Persist a new supplier via the service layer."""
        service = get_supplier_service()

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
                    "Supplier created successfully.\n\nتم إنشاء المورد بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("create", exc)

    # ========================
    # UPDATE
    # ========================

    def _edit_supplier(self) -> None:
        """Open the dialog to edit the selected supplier."""
        supplier_id = self._selected_supplier_id()
        if supplier_id is None:
            return

        db = SessionLocal()
        try:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                self._show_warning("Supplier not found. | المورد غير موجود.")
                return
            dialog = SupplierDialog(supplier=supplier, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._update_supplier(supplier_id, dialog.get_supplier_data())
        finally:
            db.close()

    def _update_supplier(self, supplier_id: Any, data: Dict[str, Any]) -> None:
        """Persist updates to an existing supplier via the service layer."""
        service = get_supplier_service()
        try:
            with session_scope() as session:
                instance, errors = service.update(session, supplier_id, data)
                if errors:
                    self._display_validation_errors(errors)
                    return
                self._show_info(
                    "Supplier updated successfully.\n\nتم تحديث المورد بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("update", exc)

    # ========================
    # DELETE
    # ========================

    def _delete_supplier(self) -> None:
        """Soft-delete the selected supplier via the service layer."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning(
                "Please select a supplier to delete. | يرجى اختيار مورد للحذف."
            )
            return

        name = self.table.item(current_row, 0).text()
        if not self._ask_confirmation(
            f"Are you sure you want to delete supplier '{name}'?\n\n"
            f"هل أنت متأكد من حذف المورد '{name}'؟",
            "Confirm Delete | تأكيد الحذف",
        ):
            return

        supplier_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        service = get_supplier_service()
        try:
            with session_scope() as session:
                success, errors = service.delete(session, supplier_id)
                if not success or errors:
                    self._display_validation_errors(errors)
                    return
                self._show_info(
                    "Supplier deleted successfully.\n\nتم حذف المورد بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("delete", exc)

    # ========================
    # VIEW
    # ========================

    def _view_item(self) -> None:
        """Show a read-only summary of the selected supplier."""
        supplier_id = self._selected_supplier_id()
        if supplier_id is None:
            return

        db = SessionLocal()
        try:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                self._show_warning("Supplier not found. | المورد غير موجود.")
                return
            terms = (
                f"{int(supplier.default_payment_terms)} days | يوم"
                if supplier.default_payment_terms is not None
                else "-"
            )
            details = (
                f"Name | الاسم: {supplier.name}\n"
                f"Contact | جهة الاتصال: {supplier.contact_name or '-'}\n"
                f"Phone | الهاتف: {supplier.phone or '-'}\n"
                f"Email | البريد: {supplier.email or '-'}\n"
                f"Tax ID | الرقم الضريبي: {supplier.tax_id or '-'}\n"
                f"Address | العنوان: {supplier.address or '-'}\n"
                f"Payment Terms | شروط الدفع: {terms}\n"
                f"Currency | العملة: {supplier.preferred_currency or '-'}\n"
                f"Status | الحالة: "
                f"{'Active | نشط' if supplier.is_active else 'Inactive | غير نشط'}"
            )
            self._show_info(details, "Supplier Details | تفاصيل المورد")
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
        logger.exception("Supplier %s error %s: %s", action, error_id, exc)
        self._show_error(
            f"Failed to {action} supplier | فشل {action} المورد\n"
            f"Error ID: {error_id}\nDetails: {exc}",
            title="Error | خطأ",
        )
