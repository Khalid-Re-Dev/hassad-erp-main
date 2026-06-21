"""
Dashboard Analytics Window

Professional interactive analytics view presenting key financial metrics,
sales statistics, customer data, and real-time session information.

Phase: F2.5 - Dashboard Analytics Modernization
Version: 1.0.0
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QFont, QColor
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from ui.base_ui import ModuleWidget
from ui.layout_components import Card, DataHeader, Spacing
from ui.animations import fade_in, sequential_card_reveal, AnimationDuration
from ui.charts_utils import (
    create_line_chart, create_bar_chart, create_pie_chart,
    ChartTheme, ChartStyle
)
from models import User, Sale, Customer, SaleLine, Payment, SaleStatus
from core.database import SessionLocal
from core.db_utils import session_scope

# Configure logging
logger = logging.getLogger(__name__)


class KPICard(Card):
    """
    Enhanced KPI card with value, label, and optional trend indicator.
    
    Features:
    - Large value display
    - Bilingual labels
    - Trend indicators (up/down)
    - Color-coded styling
    - Loading state
    """
    
    # Signals
    value_updated = pyqtSignal(str)
    
    def __init__(self, title: str, icon: str = "📊", 
                 trend_enabled: bool = False, 
                 parent: Optional[QWidget] = None):
        """
        Initialize KPI card.
        
        Args:
            title: Bilingual title (English | Arabic)
            icon: Emoji or icon character
            trend_enabled: Whether to show trend indicator
            parent: Parent widget
        """
        super().__init__(parent=parent)
        
        self.title = title
        self.icon = icon
        self.trend_enabled = trend_enabled
        self._current_value = "0"
        self._trend_value = 0.0
        
        self.setMinimumHeight(140)
        self.setMaximumHeight(180)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup KPI card UI."""
        # Main layout
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            Spacing.MEDIUM.value, Spacing.MEDIUM.value,
            Spacing.MEDIUM.value, Spacing.MEDIUM.value
        )
        layout.setSpacing(Spacing.SMALL.value)
        
        # Title row with icon
        title_layout = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(icon_label)
        
        self.title_label = QLabel(self.title)
        self.title_label.setProperty("subheading", True)
        self.title_label.setStyleSheet("font-size: 12px; color: #7f8c8d; font-weight: 600;")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Value display
        self.value_label = QLabel(self._current_value)
        value_font = QFont()
        value_font.setPointSize(32)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(self.value_label)
        
        # Trend indicator (if enabled)
        if self.trend_enabled:
            self.trend_label = QLabel("")
            self.trend_label.setStyleSheet("font-size: 11px; font-weight: 600;")
            layout.addWidget(self.trend_label)
        
        layout.addStretch()
        
        self.add_widget(content)
    
    def set_value(self, value: str, trend: Optional[float] = None):
        """
        Update KPI value and trend.
        
        Args:
            value: Display value (formatted string)
            trend: Trend percentage (positive for up, negative for down)
        """
        self._current_value = value
        self.value_label.setText(value)
        self.value_updated.emit(value)
        
        if self.trend_enabled and trend is not None:
            self._trend_value = trend
            self._update_trend_display()
    
    def _update_trend_display(self):
        """Update trend indicator display."""
        if not self.trend_enabled:
            return
        
        if self._trend_value > 0:
            arrow = "↑"
            color = "#27ae60"  # Green
            text = f"{arrow} +{abs(self._trend_value):.1f}%"
        elif self._trend_value < 0:
            arrow = "↓"
            color = "#e74c3c"  # Red
            text = f"{arrow} {abs(self._trend_value):.1f}%"
        else:
            arrow = "→"
            color = "#95a5a6"  # Gray
            text = f"{arrow} 0.0%"
        
        self.trend_label.setText(f"{text} vs last period")
        self.trend_label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {color};")
    
    def set_loading(self, loading: bool = True):
        """Show loading state."""
        if loading:
            self.value_label.setText("...")
        else:
            self.value_label.setText(self._current_value)


class DashboardWindow(ModuleWidget):
    """
    Modern interactive analytics dashboard.
    
    Features:
    - Real-time KPI cards (Sales, Customers, Invoices)
    - Financial charts (Sales trends, Payment methods, Top products)
    - Session user information
    - Auto-refresh capability
    - Responsive grid layout
    - Bilingual support
    - Theme-aware styling
    """
    
    # Signals
    data_refreshed = pyqtSignal()
    
    def __init__(self, app_context: Optional[Dict[str, Any]] = None, 
                 parent: Optional[QWidget] = None):
        """
        Initialize dashboard window.
        
        Args:
            app_context: Application context with session_factory and current_user
            parent: Parent widget
        """
        super().__init__(app_context, parent)
        
        # Store current user
        self.current_user: User = self.app_context.get('current_user')
        
        # Auto-refresh timer (every 5 minutes)
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh_view)
        self.auto_refresh_timer.start(300000)  # 5 minutes
        
        # Dashboard data cache
        self._kpi_data = {}
        self._chart_data = {}
        
        self._setup_ui()
        
        # Initial data load with delay for smooth animation
        QTimer.singleShot(100, self.refresh_view)
    
    def _setup_ui(self):
        """Setup dashboard UI with modern components."""
        self.setWindowTitle("Dashboard Analytics | لوحة التحليلات")
        
        # Main scroll area for responsive content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Content container
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(
            Spacing.LARGE.value, Spacing.LARGE.value,
            Spacing.LARGE.value, Spacing.LARGE.value
        )
        main_layout.setSpacing(Spacing.LARGE.value)
        
        # Header with session info
        header = self._create_header()
        main_layout.addWidget(header)
        
        # KPI Cards Row
        kpi_section = self._create_kpi_section()
        main_layout.addWidget(kpi_section)
        
        # Charts Grid
        charts_section = self._create_charts_section()
        main_layout.addWidget(charts_section, 1)
        
        # Set scroll widget
        scroll_area.setWidget(content_widget)
        self.main_layout.addWidget(scroll_area)
        
        # Apply fade-in animation
        QTimer.singleShot(50, lambda: fade_in(scroll_area, duration=AnimationDuration.NORMAL.value))
        
        logger.info("Dashboard UI setup completed")
    
    def _create_header(self) -> QWidget:
        """Create dashboard header with user session info."""
        header_card = Card()
        header_card.setMaximumHeight(120)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(
            Spacing.LARGE.value, Spacing.MEDIUM.value,
            Spacing.LARGE.value, Spacing.MEDIUM.value
        )
        
        # Left: Welcome message
        left_layout = QVBoxLayout()
        
        if self.current_user:
            welcome_text = f"Welcome back, {self.current_user.full_name}! | مرحباً بعودتك، {self.current_user.full_name}!"
            role_text = f"Role: {', '.join([r.name for r in self.current_user.roles])} | الدور: {', '.join([r.name for r in self.current_user.roles])}"
        else:
            welcome_text = "Welcome to Dashboard | مرحباً بك في لوحة التحكم"
            role_text = ""
        
        welcome_label = QLabel(welcome_text)
        welcome_font = QFont()
        welcome_font.setPointSize(16)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setStyleSheet("color: #2c3e50;")
        left_layout.addWidget(welcome_label)
        
        if role_text:
            role_label = QLabel(role_text)
            role_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
            left_layout.addWidget(role_label)
        
        layout.addLayout(left_layout, 1)
        
        # Right: Session info
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Current date/time
        current_time = datetime.now().strftime("%B %d, %Y - %I:%M %p")
        time_label = QLabel(f"🕐 {current_time}")
        time_label.setStyleSheet("font-size: 11px; color: #7f8c8d; font-weight: 600;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(time_label)
        
        # Branch info (if available)
        if self.current_user and self.current_user.branch:
            branch_label = QLabel(f"📍 {self.current_user.branch.name}")
            branch_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
            branch_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            right_layout.addWidget(branch_label)
        
        layout.addLayout(right_layout)
        
        header_card.add_layout(layout)
        
        return header_card
    
    def _create_kpi_section(self) -> QWidget:
        """Create KPI cards section."""
        section_container = QWidget()
        layout = QVBoxLayout(section_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MEDIUM.value)
        
        # Section title
        title_label = QLabel("📊 Key Metrics | المؤشرات الرئيسية")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # KPI cards grid
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(Spacing.MEDIUM.value)
        
        # Create KPI cards
        self.total_sales_card = KPICard(
            "Total Sales Today | إجمالي المبيعات اليوم",
            icon="💰",
            trend_enabled=True
        )
        kpi_grid.addWidget(self.total_sales_card, 0, 0)
        
        self.invoice_count_card = KPICard(
            "Invoices Today | الفواتير اليوم",
            icon="🧾",
            trend_enabled=True
        )
        kpi_grid.addWidget(self.invoice_count_card, 0, 1)
        
        self.customer_count_card = KPICard(
            "Active Customers | العملاء النشطون",
            icon="👥",
            trend_enabled=False
        )
        kpi_grid.addWidget(self.customer_count_card, 0, 2)
        
        self.avg_invoice_card = KPICard(
            "Avg Invoice Value | متوسط قيمة الفاتورة",
            icon="📈",
            trend_enabled=False
        )
        kpi_grid.addWidget(self.avg_invoice_card, 0, 3)
        
        layout.addLayout(kpi_grid)
        
        # Store cards for animation
        self.kpi_cards = [
            self.total_sales_card,
            self.invoice_count_card,
            self.customer_count_card,
            self.avg_invoice_card
        ]
        
        # Animate cards on startup
        QTimer.singleShot(100, lambda: sequential_card_reveal(
            self.kpi_cards, 
            delay_between=80, 
            animation_duration=200
        ))
        
        return section_container
    
    def _create_charts_section(self) -> QWidget:
        """Create charts grid section."""
        section_container = QWidget()
        layout = QVBoxLayout(section_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MEDIUM.value)
        
        # Section title
        title_label = QLabel("📉 Analytics | التحليلات")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Charts grid
        charts_grid = QGridLayout()
        charts_grid.setSpacing(Spacing.MEDIUM.value)
        
        # Sales Trend Chart (Line)
        self.sales_trend_card = Card("Sales Trend (7 Days) | اتجاه المبيعات (7 أيام)", collapsible=False)
        self.sales_trend_card.setMinimumHeight(350)
        self.sales_trend_chart_widget = QLabel("Loading chart... | جار تحميل الرسم البياني...")
        self.sales_trend_chart_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sales_trend_chart_widget.setStyleSheet("color: #95a5a6; font-size: 14px;")
        self.sales_trend_card.add_widget(self.sales_trend_chart_widget)
        charts_grid.addWidget(self.sales_trend_card, 0, 0, 1, 2)
        
        # Payment Methods Chart (Pie)
        self.payment_methods_card = Card("Payment Methods | طرق الدفع", collapsible=False)
        self.payment_methods_card.setMinimumHeight(350)
        self.payment_methods_chart_widget = QLabel("Loading chart... | جار تحميل الرسم البياني...")
        self.payment_methods_chart_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.payment_methods_chart_widget.setStyleSheet("color: #95a5a6; font-size: 14px;")
        self.payment_methods_card.add_widget(self.payment_methods_chart_widget)
        charts_grid.addWidget(self.payment_methods_card, 1, 0)
        
        # Top Products Chart (Bar)
        self.top_products_card = Card("Top Selling Products | أكثر المنتجات مبيعاً", collapsible=False)
        self.top_products_card.setMinimumHeight(350)
        self.top_products_chart_widget = QLabel("Loading chart... | جار تحميل الرسم البياني...")
        self.top_products_chart_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top_products_chart_widget.setStyleSheet("color: #95a5a6; font-size: 14px;")
        self.top_products_card.add_widget(self.top_products_chart_widget)
        charts_grid.addWidget(self.top_products_card, 1, 1)
        
        layout.addLayout(charts_grid, 1)
        
        return section_container
    
    def load_data(self, session: Session) -> None:
        """
        Load dashboard data from database.
        
        Args:
            session: Active database session
        """
        try:
            logger.info("Loading dashboard data...")
            
            # Load KPI data
            self._load_kpi_data(session)
            
            # Load chart data
            self._load_chart_data(session)
            
            # Update UI
            self._update_kpi_cards()
            self._update_charts()
            
            self.data_refreshed.emit()
            logger.info("Dashboard data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}", exc_info=True)
            raise
    
    def _load_kpi_data(self, session: Session):
        """Load KPI metrics from database."""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Current user's branch filter (if available)
        branch_filter = []
        if self.current_user and self.current_user.branch_id:
            branch_filter.append(Sale.branch_id == self.current_user.branch_id)
        
        # Total Sales Today
        today_sales = session.query(
            func.coalesce(func.sum(Sale.grand_total), 0)
        ).filter(
            and_(
                func.date(Sale.invoice_date) == today,
                Sale.status == SaleStatus.POSTED,
                *branch_filter
            )
        ).scalar() or Decimal('0')
        
        # Yesterday's sales for comparison
        yesterday_sales = session.query(
            func.coalesce(func.sum(Sale.grand_total), 0)
        ).filter(
            and_(
                func.date(Sale.invoice_date) == yesterday,
                Sale.status == SaleStatus.POSTED,
                *branch_filter
            )
        ).scalar() or Decimal('0')
        
        # Calculate trend
        if yesterday_sales > 0:
            sales_trend = float((today_sales - yesterday_sales) / yesterday_sales * 100)
        else:
            sales_trend = 0.0
        
        # Invoice Count Today
        today_invoices = session.query(func.count(Sale.id)).filter(
            and_(
                func.date(Sale.invoice_date) == today,
                Sale.status == SaleStatus.POSTED,
                *branch_filter
            )
        ).scalar() or 0
        
        # Yesterday's invoices
        yesterday_invoices = session.query(func.count(Sale.id)).filter(
            and_(
                func.date(Sale.invoice_date) == yesterday,
                Sale.status == SaleStatus.POSTED,
                *branch_filter
            )
        ).scalar() or 0
        
        # Invoice trend
        if yesterday_invoices > 0:
            invoice_trend = float((today_invoices - yesterday_invoices) / yesterday_invoices * 100)
        else:
            invoice_trend = 0.0
        
        # Active Customers Count
        active_customers = session.query(func.count(Customer.id)).filter(
            Customer.is_active == True
        ).scalar() or 0
        
        # Average Invoice Value
        if today_invoices > 0:
            avg_invoice = float(today_sales / today_invoices)
        else:
            avg_invoice = 0.0
        
        # Store KPI data
        self._kpi_data = {
            'total_sales': float(today_sales),
            'sales_trend': sales_trend,
            'invoice_count': today_invoices,
            'invoice_trend': invoice_trend,
            'customer_count': active_customers,
            'avg_invoice': avg_invoice
        }
        
        logger.debug(f"KPI data loaded: {self._kpi_data}")
    
    def _load_chart_data(self, session: Session):
        """Load chart data from database."""
        # Branch filter
        branch_filter = []
        if self.current_user and self.current_user.branch_id:
            branch_filter.append(Sale.branch_id == self.current_user.branch_id)
        
        # Sales Trend (Last 7 days)
        sales_trend_data = []
        for i in range(6, -1, -1):
            date = datetime.now().date() - timedelta(days=i)
            daily_total = session.query(
                func.coalesce(func.sum(Sale.grand_total), 0)
            ).filter(
                and_(
                    func.date(Sale.invoice_date) == date,
                    Sale.status == SaleStatus.POSTED,
                    *branch_filter
                )
            ).scalar() or Decimal('0')
            
            sales_trend_data.append({
                'date': date.strftime('%m/%d'),
                'value': float(daily_total)
            })
        
        # Payment Methods Distribution
        payment_methods = session.query(
            Payment.method,
            func.sum(Payment.amount).label('total')
        ).join(Sale).filter(
            and_(
                Sale.status == SaleStatus.POSTED,
                *branch_filter
            )
        ).group_by(Payment.method).all()
        
        payment_data = [
            {'method': method.value, 'total': float(total)}
            for method, total in payment_methods
        ]
        
        # Top 5 Products
        top_products = session.query(
            SaleLine.product_name,
            func.sum(SaleLine.quantity).label('total_qty'),
            func.sum(SaleLine.line_total).label('total_amount')
        ).join(Sale).filter(
            and_(
                Sale.status == SaleStatus.POSTED,
                func.date(Sale.invoice_date) >= (datetime.now().date() - timedelta(days=7)),
                *branch_filter
            )
        ).group_by(SaleLine.product_name).order_by(
            func.sum(SaleLine.line_total).desc()
        ).limit(5).all()
        
        products_data = [
            {
                'name': name[:20] + '...' if len(name) > 20 else name,
                'quantity': float(qty),
                'amount': float(amount)
            }
            for name, qty, amount in top_products
        ]
        
        # Store chart data
        self._chart_data = {
            'sales_trend': sales_trend_data,
            'payment_methods': payment_data,
            'top_products': products_data
        }
        
        logger.debug(f"Chart data loaded: {len(sales_trend_data)} trend points, "
                    f"{len(payment_data)} payment methods, {len(products_data)} products")
    
    def _update_kpi_cards(self):
        """Update KPI card values."""
        # Total Sales
        total_sales = self._kpi_data.get('total_sales', 0)
        sales_trend = self._kpi_data.get('sales_trend', 0)
        self.total_sales_card.set_value(
            f"${total_sales:,.2f}",
            trend=sales_trend
        )
        
        # Invoice Count
        invoice_count = self._kpi_data.get('invoice_count', 0)
        invoice_trend = self._kpi_data.get('invoice_trend', 0)
        self.invoice_count_card.set_value(
            str(invoice_count),
            trend=invoice_trend
        )
        
        # Customer Count
        customer_count = self._kpi_data.get('customer_count', 0)
        self.customer_count_card.set_value(str(customer_count))
        
        # Average Invoice
        avg_invoice = self._kpi_data.get('avg_invoice', 0)
        self.avg_invoice_card.set_value(f"${avg_invoice:,.2f}")
    
    def _update_charts(self):
        """Update chart visualizations."""
        # Sales Trend Chart
        sales_data = self._chart_data.get('sales_trend', [])
        if sales_data:
            try:
                sales_chart = create_line_chart(
                    data=sales_data,
                    x_key='date',
                    y_key='value',
                    title="Daily Sales",
                    x_label="Date",
                    y_label="Amount ($)",
                    theme=ChartTheme.MODERN
                )
                
                # Replace placeholder with chart
                self.sales_trend_card.body_layout.removeWidget(self.sales_trend_chart_widget)
                self.sales_trend_chart_widget.deleteLater()
                self.sales_trend_chart_widget = sales_chart
                self.sales_trend_card.add_widget(sales_chart)
                
                logger.debug("Sales trend chart updated")
            except Exception as e:
                logger.error(f"Error creating sales trend chart: {e}")
                self.sales_trend_chart_widget.setText(f"Chart error: {str(e)}")
        
        # Payment Methods Chart
        payment_data = self._chart_data.get('payment_methods', [])
        if payment_data:
            try:
                payment_chart = create_pie_chart(
                    data=payment_data,
                    label_key='method',
                    value_key='total',
                    title="Payment Distribution",
                    theme=ChartTheme.MODERN
                )
                
                # Replace placeholder with chart
                self.payment_methods_card.body_layout.removeWidget(self.payment_methods_chart_widget)
                self.payment_methods_chart_widget.deleteLater()
                self.payment_methods_chart_widget = payment_chart
                self.payment_methods_card.add_widget(payment_chart)
                
                logger.debug("Payment methods chart updated")
            except Exception as e:
                logger.error(f"Error creating payment methods chart: {e}")
                self.payment_methods_chart_widget.setText(f"Chart error: {str(e)}")
        
        # Top Products Chart
        products_data = self._chart_data.get('top_products', [])
        if products_data:
            try:
                products_chart = create_bar_chart(
                    data=products_data,
                    x_key='name',
                    y_key='amount',
                    title="Top Products by Revenue",
                    x_label="Product",
                    y_label="Revenue ($)",
                    theme=ChartTheme.MODERN
                )
                
                # Replace placeholder with chart
                self.top_products_card.body_layout.removeWidget(self.top_products_chart_widget)
                self.top_products_chart_widget.deleteLater()
                self.top_products_chart_widget = products_chart
                self.top_products_card.add_widget(products_chart)
                
                logger.debug("Top products chart updated")
            except Exception as e:
                logger.error(f"Error creating top products chart: {e}")
                self.top_products_chart_widget.setText(f"Chart error: {str(e)}")
    
    def refresh_view(self) -> None:
        """Refresh dashboard data (override from ModuleUI)."""
        logger.info("Refreshing dashboard...")
        super().refresh_view()
    
    def closeEvent(self, event):
        """Clean up on close."""
        self.auto_refresh_timer.stop()
        super().closeEvent(event)


# Convenience function for easy instantiation
def create_dashboard(user: User, parent: Optional[QWidget] = None) -> DashboardWindow:
    """
    Create dashboard window with user context.
    
    Args:
        user: Current user
        parent: Parent widget
        
    Returns:
        DashboardWindow instance
    """
    app_context = {
        'session_factory': SessionLocal,
        'current_user': user,
        'current_branch': user.branch if user else None
    }
    
    return DashboardWindow(app_context=app_context, parent=parent)
