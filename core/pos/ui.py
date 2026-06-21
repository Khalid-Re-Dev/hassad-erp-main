"""
POS UI Components (PyQt6)
Desktop cashier interface for point-of-sale operations
"""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
        QDialog, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox,
        QTextEdit, QGroupBox, QScrollArea
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QKeySequence, QShortcut
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


if PYQT_AVAILABLE:
    
    class POSMainWindow(QMainWindow):
        """
        Main POS window with product selection, cart, and payment
        """
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Hassad POS - Point of Sale")
            self.setGeometry(100, 100, 1400, 900)
            
            # Initialize cart
            self.cart_items = []
            self.current_customer = None
            
            # Setup UI
            self._setup_ui()
            self._setup_shortcuts()
            
        def _setup_ui(self):
            """Setup main UI layout"""
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            main_layout = QHBoxLayout(central_widget)
            
            # Left panel - Product selection
            left_panel = self._create_product_panel()
            main_layout.addWidget(left_panel, stretch=2)
            
            # Right panel - Cart and totals
            right_panel = self._create_cart_panel()
            main_layout.addWidget(right_panel, stretch=1)
            
        def _create_product_panel(self) -> QWidget:
            """Create product selection panel"""
            panel = QWidget()
            layout = QVBoxLayout(panel)
            
            # Search bar
            search_layout = QHBoxLayout()
            search_label = QLabel("Search (F2):")
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Scan barcode or search product...")
            self.search_input.returnPressed.connect(self._on_search)
            
            search_layout.addWidget(search_label)
            search_layout.addWidget(self.search_input)
            layout.addLayout(search_layout)
            
            # Product grid (quick keys)
            products_group = QGroupBox("Quick Products")
            products_layout = QGridLayout()
            
            # Sample quick product buttons (would be loaded from database)
            quick_products = [
                ("Product A", "100.00"),
                ("Product B", "60.00"),
                ("Product C", "150.00"),
                ("Product D", "45.00"),
                ("Product E", "80.00"),
                ("Product F", "120.00"),
            ]
            
            row, col = 0, 0
            for name, price in quick_products:
                btn = QPushButton(f"{name}\n{price} SAR")
                btn.setMinimumHeight(80)
                btn.setFont(QFont("Arial", 12))
                btn.clicked.connect(lambda checked, n=name, p=price: self._add_quick_product(n, p))
                products_layout.addWidget(btn, row, col)
                
                col += 1
                if col > 2:
                    col = 0
                    row += 1
            
            products_group.setLayout(products_layout)
            layout.addWidget(products_group)
            
            return panel
        
        def _create_cart_panel(self) -> QWidget:
            """Create cart and checkout panel"""
            panel = QWidget()
            layout = QVBoxLayout(panel)
            
            # Customer info
            customer_layout = QHBoxLayout()
            customer_label = QLabel("Customer:")
            self.customer_combo = QComboBox()
            self.customer_combo.addItem("Walk-in Customer")
            customer_layout.addWidget(customer_label)
            customer_layout.addWidget(self.customer_combo)
            layout.addLayout(customer_layout)
            
            # Cart table
            cart_label = QLabel("Cart Items")
            cart_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            layout.addWidget(cart_label)
            
            self.cart_table = QTableWidget()
            self.cart_table.setColumnCount(5)
            self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Total", ""])
            self.cart_table.setColumnWidth(0, 150)
            self.cart_table.setColumnWidth(1, 60)
            self.cart_table.setColumnWidth(2, 80)
            self.cart_table.setColumnWidth(3, 80)
            self.cart_table.setColumnWidth(4, 60)
            layout.addWidget(self.cart_table)
            
            # Totals
            totals_group = QGroupBox("Totals")
            totals_layout = QVBoxLayout()
            
            self.subtotal_label = QLabel("Subtotal: 0.00 SAR")
            self.discount_label = QLabel("Discount: 0.00 SAR")
            self.tax_label = QLabel("Tax (15%): 0.00 SAR")
            self.total_label = QLabel("TOTAL: 0.00 SAR")
            self.total_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            
            totals_layout.addWidget(self.subtotal_label)
            totals_layout.addWidget(self.discount_label)
            totals_layout.addWidget(self.tax_label)
            totals_layout.addWidget(self.total_label)
            
            totals_group.setLayout(totals_layout)
            layout.addWidget(totals_group)
            
            # Action buttons
            actions_layout = QVBoxLayout()
            
            self.discount_btn = QPushButton("Apply Discount (F3)")
            self.discount_btn.setMinimumHeight(50)
            self.discount_btn.clicked.connect(self._apply_discount)
            
            self.payment_btn = QPushButton("Payment (F4)")
            self.payment_btn.setMinimumHeight(50)
            self.payment_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px;")
            self.payment_btn.clicked.connect(self._open_payment_dialog)
            
            self.clear_btn = QPushButton("Clear Cart (F5)")
            self.clear_btn.setMinimumHeight(50)
            self.clear_btn.clicked.connect(self._clear_cart)
            
            actions_layout.addWidget(self.discount_btn)
            actions_layout.addWidget(self.payment_btn)
            actions_layout.addWidget(self.clear_btn)
            
            layout.addLayout(actions_layout)
            
            return panel
        
        def _setup_shortcuts(self):
            """Setup keyboard shortcuts"""
            QShortcut(QKeySequence("F2"), self).activated.connect(lambda: self.search_input.setFocus())
            QShortcut(QKeySequence("F3"), self).activated.connect(self._apply_discount)
            QShortcut(QKeySequence("F4"), self).activated.connect(self._open_payment_dialog)
            QShortcut(QKeySequence("F5"), self).activated.connect(self._clear_cart)
        
        def _on_search(self):
            """Handle product search"""
            search_text = self.search_input.text().strip()
            if not search_text:
                return
            
            # TODO: Search product by barcode or name in database
            # For now, show placeholder
            QMessageBox.information(self, "Search", f"Searching for: {search_text}")
            self.search_input.clear()
        
        def _add_quick_product(self, name: str, price: str):
            """Add quick product to cart"""
            # TODO: Load actual product from database
            self._add_to_cart({
                'name': name,
                'sku': 'PROD-001',
                'quantity': 1,
                'price': Decimal(price),
            })
        
        def _add_to_cart(self, product: dict):
            """Add product to cart"""
            self.cart_items.append(product)
            self._update_cart_display()
            self._calculate_totals()
        
        def _update_cart_display(self):
            """Update cart table display"""
            self.cart_table.setRowCount(len(self.cart_items))
            
            for row, item in enumerate(self.cart_items):
                self.cart_table.setItem(row, 0, QTableWidgetItem(item['name']))
                self.cart_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
                self.cart_table.setItem(row, 2, QTableWidgetItem(f"{item['price']:.2f}"))
                
                total = item['quantity'] * item['price']
                self.cart_table.setItem(row, 3, QTableWidgetItem(f"{total:.2f}"))
                
                # Remove button
                remove_btn = QPushButton("X")
                remove_btn.clicked.connect(lambda checked, r=row: self._remove_from_cart(r))
                self.cart_table.setCellWidget(row, 4, remove_btn)
        
        def _remove_from_cart(self, row: int):
            """Remove item from cart"""
            if 0 <= row < len(self.cart_items):
                self.cart_items.pop(row)
                self._update_cart_display()
                self._calculate_totals()
        
        def _calculate_totals(self):
            """Calculate and display totals"""
            subtotal = sum(item['quantity'] * item['price'] for item in self.cart_items)
            discount = Decimal('0.00')  # TODO: Apply discount logic
            tax = subtotal * Decimal('0.15')  # 15% VAT
            total = subtotal - discount + tax
            
            self.subtotal_label.setText(f"Subtotal: {subtotal:.2f} SAR")
            self.discount_label.setText(f"Discount: {discount:.2f} SAR")
            self.tax_label.setText(f"Tax (15%): {tax:.2f} SAR")
            self.total_label.setText(f"TOTAL: {total:.2f} SAR")
        
        def _apply_discount(self):
            """Open discount dialog"""
            # TODO: Implement discount dialog
            QMessageBox.information(self, "Discount", "Discount dialog not yet implemented")
        
        def _open_payment_dialog(self):
            """Open payment dialog"""
            if not self.cart_items:
                QMessageBox.warning(self, "Empty Cart", "Please add items to cart first")
                return
            
            # Calculate total
            subtotal = sum(item['quantity'] * item['price'] for item in self.cart_items)
            tax = subtotal * Decimal('0.15')
            total = subtotal + tax
            
            dialog = PaymentDialog(total, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Process payment
                self._process_sale(dialog.get_payments())
        
        def _process_sale(self, payments: List[dict]):
            """Process the sale"""
            # TODO: Call POS service to create sale
            QMessageBox.information(self, "Success", "Sale completed successfully!")
            self._clear_cart()
        
        def _clear_cart(self):
            """Clear cart"""
            self.cart_items.clear()
            self._update_cart_display()
            self._calculate_totals()
    
    
    class PaymentDialog(QDialog):
        """
        Payment dialog for multi-payment support
        """
        
        def __init__(self, total_amount: Decimal, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Payment")
            self.setModal(True)
            self.setMinimumWidth(500)
            
            self.total_amount = total_amount
            self.payments = []
            
            self._setup_ui()
        
        def _setup_ui(self):
            """Setup payment dialog UI"""
            layout = QVBoxLayout(self)
            
            # Total amount
            total_label = QLabel(f"Total Amount: {self.total_amount:.2f} SAR")
            total_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            layout.addWidget(total_label)
            
            # Payment method
            method_layout = QHBoxLayout()
            method_label = QLabel("Payment Method:")
            self.method_combo = QComboBox()
            self.method_combo.addItems(["Cash", "Card", "Credit"])
            method_layout.addWidget(method_label)
            method_layout.addWidget(self.method_combo)
            layout.addLayout(method_layout)
            
            # Amount
            amount_layout = QHBoxLayout()
            amount_label = QLabel("Amount:")
            self.amount_input = QDoubleSpinBox()
            self.amount_input.setMaximum(999999.99)
            self.amount_input.setValue(float(self.total_amount))
            self.amount_input.setDecimals(2)
            amount_layout.addWidget(amount_label)
            amount_layout.addWidget(self.amount_input)
            layout.addLayout(amount_layout)
            
            # Payments list
            self.payments_table = QTableWidget()
            self.payments_table.setColumnCount(3)
            self.payments_table.setHorizontalHeaderLabels(["Method", "Amount", ""])
            layout.addWidget(self.payments_table)
            
            # Add payment button
            add_btn = QPushButton("Add Payment")
            add_btn.clicked.connect(self._add_payment)
            layout.addWidget(add_btn)
            
            # Remaining amount
            self.remaining_label = QLabel(f"Remaining: {self.total_amount:.2f} SAR")
            self.remaining_label.setFont(QFont("Arial", 14))
            layout.addWidget(self.remaining_label)
            
            # Complete button
            complete_btn = QPushButton("Complete Payment")
            complete_btn.setMinimumHeight(50)
            complete_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            complete_btn.clicked.connect(self._complete_payment)
            layout.addWidget(complete_btn)
        
        def _add_payment(self):
            """Add payment to list"""
            method = self.method_combo.currentText()
            amount = Decimal(str(self.amount_input.value()))
            
            self.payments.append({
                'method': method,
                'amount': amount,
            })
            
            self._update_payments_display()
        
        def _update_payments_display(self):
            """Update payments table"""
            self.payments_table.setRowCount(len(self.payments))
            
            total_paid = Decimal('0.00')
            for row, payment in enumerate(self.payments):
                self.payments_table.setItem(row, 0, QTableWidgetItem(payment['method']))
                self.payments_table.setItem(row, 1, QTableWidgetItem(f"{payment['amount']:.2f}"))
                
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, r=row: self._remove_payment(r))
                self.payments_table.setCellWidget(row, 2, remove_btn)
                
                total_paid += payment['amount']
            
            remaining = self.total_amount - total_paid
            self.remaining_label.setText(f"Remaining: {remaining:.2f} SAR")
        
        def _remove_payment(self, row: int):
            """Remove payment from list"""
            if 0 <= row < len(self.payments):
                self.payments.pop(row)
                self._update_payments_display()
        
        def _complete_payment(self):
            """Complete payment"""
            total_paid = sum(p['amount'] for p in self.payments)
            
            if total_paid < self.total_amount:
                QMessageBox.warning(self, "Insufficient Payment", 
                                  f"Total paid ({total_paid:.2f}) is less than amount due ({self.total_amount:.2f})")
                return
            
            self.accept()
        
        def get_payments(self) -> List[dict]:
            """Get list of payments"""
            return self.payments


else:
    # Placeholder classes when PyQt6 not available
    class POSMainWindow:
        def __init__(self):
            raise ImportError("PyQt6 not installed. Install with: pip install PyQt6")
    
    class PaymentDialog:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 not installed. Install with: pip install PyQt6")
