# GENERATED/UPDATED BY PHASE B RESUME: 2025-11-02T07:27:06Z
"""Chart of Accounts Window.

Provides full CRUD management for the Chart of Accounts: create, edit, delete
(system-protected, soft by default), search, filter and view, wired to
:class:`AccountService`. All accounting-safety business logic lives in the
service layer; this module only handles presentation.

Phase F2.3 - Modernized with layout components and animations.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt, QTimer
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
from core.services import get_account_service, ValidationError
from models import Account, AccountType
from ui.base_ui import ModuleWidget
from ui.layout_components import Card, Toolbar, FilterBar, DataHeader, Spacing
from ui.animations import fade_in, AnimationDuration

logger = logging.getLogger(__name__)


# Bilingual labels for each account type (display label -> enum member).
ACCOUNT_TYPE_LABELS = [
    ("Asset | الأصول", AccountType.ASSET),
    ("Liability | الخصوم", AccountType.LIABILITY),
    ("Equity | حقوق الملكية", AccountType.EQUITY),
    ("Revenue | الإيرادات", AccountType.REVENUE),
    ("Expense | المصروفات", AccountType.EXPENSE),
]


class AccountDialog(QDialog):
    """Dialog for creating/editing a chart-of-accounts entry."""

    def __init__(
        self,
        account: Optional[Account] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the dialog.

        Args:
            account: Existing account to edit, or None to create a new one.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.account = account
        self.is_edit = account is not None
        self._setup_ui()
        self._load_parent_options()
        if self.is_edit:
            self._load_account_data()

    def _setup_ui(self) -> None:
        """Build the form UI."""
        self.setWindowTitle(
            "Edit Account | تعديل الحساب"
            if self.is_edit
            else "Create Account | إنشاء حساب"
        )
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Code (required, unique per company).
        self.code_input = QLineEdit()
        form.addRow("Code | الرمز *", self.code_input)

        # Name (English, required).
        self.name_en_input = QLineEdit()
        form.addRow("Name (English) | الاسم (إنجليزي) *", self.name_en_input)

        # Name (Arabic).
        self.name_ar_input = QLineEdit()
        form.addRow("Name (Arabic) | الاسم (عربي)", self.name_ar_input)

        # Account type (required).
        self.type_combo = QComboBox()
        for label, member in ACCOUNT_TYPE_LABELS:
            self.type_combo.addItem(label, member)
        form.addRow("Account Type | نوع الحساب *", self.type_combo)

        # Parent account (optional).
        self.parent_combo = QComboBox()
        form.addRow("Parent Account | الحساب الأب", self.parent_combo)

        # Description.
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Optional | اختياري")
        form.addRow("Description | الوصف", self.description_input)

        # Active.
        self.active_checkbox = QCheckBox("Active | نشط")
        self.active_checkbox.setChecked(True)
        form.addRow("", self.active_checkbox)

        # Read-only note for editing the type of a posted account.
        self.type_note = QLabel(
            "Note: type cannot be changed after journal entries exist.\n"
            "ملاحظة: لا يمكن تغيير النوع بعد وجود قيود."
        )
        self.type_note.setStyleSheet("color: gray; font-size: 11px;")
        self.type_note.setVisible(self.is_edit)
        form.addRow("", self.type_note)

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
        """Load available parent accounts into the combo box."""
        self.parent_combo.addItem("-- No Parent | بدون أب --", None)
        db = SessionLocal()
        try:
            query = db.query(Account).filter(Account.is_active == True)
            # An account cannot be its own parent.
            if self.is_edit and self.account is not None:
                query = query.filter(Account.id != self.account.id)
            for account in query.order_by(Account.code).all():
                type_value = (
                    account.account_type.value if account.account_type else ""
                )
                label = f"{account.code} - {account.name_en} ({type_value})"
                self.parent_combo.addItem(label, account.id)
        finally:
            db.close()

    def _load_account_data(self) -> None:
        """Populate the form with the existing account's values."""
        if not self.account:
            return
        self.code_input.setText(self.account.code or "")
        self.name_en_input.setText(self.account.name_en or "")
        self.name_ar_input.setText(self.account.name_ar or "")
        self.description_input.setPlainText(self.account.description or "")
        self.active_checkbox.setChecked(bool(self.account.is_active))

        # Select current type.
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.account.account_type:
                self.type_combo.setCurrentIndex(i)
                break

        # Select current parent.
        if self.account.parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self.account.parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break

    def get_account_data(self) -> Dict[str, Any]:
        """Collect form values into a service-ready dictionary."""
        return {
            "code": self.code_input.text().strip(),
            "name_en": self.name_en_input.text().strip(),
            "name_ar": self.name_ar_input.text().strip() or None,
            "account_type": self.type_combo.currentData(),
            "parent_id": self.parent_combo.currentData(),
            "description": self.description_input.toPlainText().strip() or None,
            "is_active": self.active_checkbox.isChecked(),
        }


class AccountsWindow(ModuleWidget):
    """
    Chart of Accounts management window with full CRUD.

    Features:
    - Account hierarchy management
    - Account creation and editing
    - Account type classification and filtering
    """

    def __init__(self, app_context: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(app_context, parent)
        self.setWindowTitle("Chart of Accounts | شجرة الحسابات")
        self._setup_ui()
        self.refresh_view()

    def _setup_ui(self):
        """Setup modern user interface with components."""
        # Page Header
        header = DataHeader(
            title="Chart of Accounts | شجرة الحسابات",
            subtitle="0 accounts | 0 حساب"
        )
        self.main_layout.addWidget(header)

        # Main Content Card
        main_card = Card()

        # Toolbar
        toolbar = Toolbar()
        toolbar.add_action("Add Account | إضافة حساب", self._add_account, primary=True)
        toolbar.add_action("View | عرض", self._view_item)
        toolbar.add_action("Edit | تعديل", self._edit_account)
        toolbar.add_action("Delete | حذف", self._delete_account, danger=True)
        toolbar.add_spacer()
        toolbar.add_action("Refresh | تحديث", self.refresh_view)
        main_card.add_widget(toolbar)

        # Filter Bar
        filter_bar = FilterBar("Search accounts... | البحث في الحسابات...")
        filter_bar.search_changed.connect(self._on_search)
        filter_bar.add_filter(
            "Type | النوع",
            [
                "All | الكل",
                "Asset | الأصول",
                "Liability | الخصوم",
                "Equity | حقوق الملكية",
                "Revenue | الإيرادات",
                "Expense | المصروفات"
            ],
            self._on_type_filter
        )
        filter_bar.add_filter(
            "Level | المستوى",
            ["All | الكل", "Top Level | المستوى الأول", "Sub-Accounts | حسابات فرعية"],
            self._on_level_filter
        )
        main_card.add_widget(filter_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Code | الرمز",
            "Name | الاسم",
            "Type | النوع",
            "Parent | الحساب الأب",
            "Status | الحالة"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit_account)
        main_card.add_widget(self.table)

        self.main_layout.addWidget(main_card)

        # Store references for updates
        self.header = header
        self.main_card = main_card
        self.filter_bar = filter_bar
        self.search_input = filter_bar.search_field  # Maintain compatibility
        self._type_filter = "All"
        self._level_filter = "All"

        # Apply fade-in animation
        QTimer.singleShot(50, lambda: fade_in(main_card, duration=AnimationDuration.NORMAL.value))

    def _on_search(self, text: str):
        """Handle search text changes."""
        self.refresh_view()

    def _on_type_filter(self, label: str, value: str):
        """Handle account type filter changes."""
        self._type_filter = value
        self.refresh_view()

    def _on_level_filter(self, label: str, value: str):
        """Handle account level filter changes."""
        self._level_filter = value
        self.refresh_view()

    # ========================
    # Data loading
    # ========================

    def load_data(self, session: Session) -> None:
        """
        Load accounts data from database with filtering.

        Args:
            session: Database session
        """
        query = session.query(Account)

        # Apply search filter
        search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
        if search_term:
            query = query.filter(
                (Account.code.ilike(f"%{search_term}%")) |
                (Account.name_en.ilike(f"%{search_term}%")) |
                (Account.name_ar.ilike(f"%{search_term}%"))
            )

        # Apply type filter
        if hasattr(self, '_type_filter') and self._type_filter != "All" and "All" not in self._type_filter:
            type_map = {
                "Asset": AccountType.ASSET, "الأصول": AccountType.ASSET,
                "Liability": AccountType.LIABILITY, "الخصوم": AccountType.LIABILITY,
                "Equity": AccountType.EQUITY, "حقوق الملكية": AccountType.EQUITY,
                "Revenue": AccountType.REVENUE, "الإيرادات": AccountType.REVENUE,
                "Expense": AccountType.EXPENSE, "المصروفات": AccountType.EXPENSE,
            }
            for key, acc_type in type_map.items():
                if key in self._type_filter:
                    query = query.filter(Account.account_type == acc_type)
                    break

        # Apply level filter
        if hasattr(self, '_level_filter'):
            if "Top Level" in self._level_filter or "المستوى الأول" in self._level_filter:
                query = query.filter(Account.parent_id == None)
            elif "Sub-Accounts" in self._level_filter or "حسابات فرعية" in self._level_filter:
                query = query.filter(Account.parent_id != None)

        results = query.order_by(Account.code).limit(500).all()

        if not hasattr(self, 'table'):
            return

        # id -> code map for resolving parent codes cheaply.
        code_by_id = {a.id: a.code for a in results}

        self.table.setRowCount(len(results))
        for row, account in enumerate(results):
            name = account.name_en or "N/A"
            if account.name_ar:
                name = f"{name} | {account.name_ar}"
            type_name = account.account_type.value if account.account_type else "N/A"

            parent_code = ""
            if account.parent_id:
                parent_code = code_by_id.get(account.parent_id, "")
                if not parent_code:
                    try:
                        parent_code = account.parent.code if account.parent else ""
                    except Exception:  # noqa: BLE001
                        parent_code = ""

            self.table.setItem(row, 0, QTableWidgetItem(str(account.code or "")))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(type_name))
            self.table.setItem(row, 3, QTableWidgetItem(parent_code))
            self.table.setItem(
                row, 4,
                QTableWidgetItem("Active | نشط" if account.is_active else "Inactive | غير نشط")
            )
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, account.id)

        if hasattr(self, 'header'):
            self.header.set_count(len(results), "accounts | حسابات")

    def _selected_account_id(self) -> Optional[Any]:
        """Return the id of the currently selected row, or None."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning("Please select an account first. | يرجى اختيار حساب أولاً.")
            return None
        return self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

    # ========================
    # CREATE
    # ========================

    def _add_account(self):
        """Open the dialog to create a new account."""
        dialog = AccountDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._save_account(dialog.get_account_data())

    def _save_account(self, data: Dict[str, Any]) -> None:
        """Persist a new account via the service layer."""
        service = get_account_service()

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
                    "Account created successfully.\n\nتم إنشاء الحساب بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("create", exc)

    # ========================
    # UPDATE
    # ========================

    def _edit_account(self):
        """Open the dialog to edit the selected account."""
        account_id = self._selected_account_id()
        if account_id is None:
            return

        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                self._show_warning("Account not found. | الحساب غير موجود.")
                return
            dialog = AccountDialog(account=account, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._update_account(account_id, dialog.get_account_data())
        finally:
            db.close()

    def _update_account(self, account_id: Any, data: Dict[str, Any]) -> None:
        """Persist updates to an existing account via the service layer."""
        service = get_account_service()
        try:
            with session_scope() as session:
                instance, errors = service.update(session, account_id, data)
                if errors:
                    self._display_validation_errors(errors)
                    return
                self._show_info(
                    "Account updated successfully.\n\nتم تحديث الحساب بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("update", exc)

    # ========================
    # DELETE
    # ========================

    def _delete_account(self):
        """Delete (soft) the selected account via the service layer."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._show_warning("Please select an account to delete. | يرجى اختيار حساب للحذف.")
            return

        code = self.table.item(current_row, 0).text()
        if not self._ask_confirmation(
            f"Are you sure you want to delete account '{code}'?\n\n"
            f"هل أنت متأكد من حذف الحساب '{code}'؟",
            "Confirm Delete | تأكيد الحذف",
        ):
            return

        account_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        service = get_account_service()
        try:
            with session_scope() as session:
                success, errors = service.delete(session, account_id)
                if not success or errors:
                    self._display_validation_errors(errors)
                    return
                self._show_info(
                    "Account deleted successfully.\n\nتم حذف الحساب بنجاح.",
                    "Success | نجاح",
                )
                self.refresh_view()
        except Exception as exc:  # noqa: BLE001
            self._handle_unexpected_error("delete", exc)

    # ========================
    # VIEW
    # ========================

    def _view_item(self):
        """Show a read-only summary of the selected account."""
        account_id = self._selected_account_id()
        if account_id is None:
            return

        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                self._show_warning("Account not found. | الحساب غير موجود.")
                return
            parent_code = "-"
            try:
                parent_code = account.parent.code if account.parent else "-"
            except Exception:  # noqa: BLE001
                parent_code = "-"
            type_value = account.account_type.value if account.account_type else "-"
            details = (
                f"Code | الرمز: {account.code}\n"
                f"Name (EN) | الاسم: {account.name_en}\n"
                f"Name (AR) | الاسم (عربي): {account.name_ar or '-'}\n"
                f"Type | النوع: {type_value}\n"
                f"Parent | الحساب الأب: {parent_code}\n"
                f"System | حساب نظام: {'Yes | نعم' if account.is_system else 'No | لا'}\n"
                f"Description | الوصف: {account.description or '-'}\n"
                f"Status | الحالة: "
                f"{'Active | نشط' if account.is_active else 'Inactive | غير نشط'}"
            )
            self._show_info(details, "Account Details | تفاصيل الحساب")
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
            "Validation errors occurred:\n" + "\n".join(en_msgs) +
            "\n\nحدثت أخطاء في التحقق:\n" + "\n".join(ar_msgs)
        )
        self._show_error(message, title="Validation | التحقق")

    def _handle_unexpected_error(self, action: str, exc: Exception) -> None:
        """Log and surface an unexpected error with a trace id."""
        error_id = str(uuid.uuid4())[:8]
        logger.exception("Account %s error %s: %s", action, error_id, exc)
        self._show_error(
            f"Failed to {action} account | فشل {action} الحساب\n"
            f"Error ID: {error_id}\nDetails: {exc}",
            title="Error | خطأ",
        )
