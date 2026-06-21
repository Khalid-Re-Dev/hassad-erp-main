# Phase F2.5 - Dashboard Analytics Modernization

## 📋 Overview

This document details the implementation of the modern, interactive analytics dashboard for Hassad ERP System. The dashboard provides real-time financial metrics, sales statistics, and data visualizations in a professional, user-friendly interface.

**Phase**: F2.5 - Dashboard Analytics Modernization  
**Version**: 1.0.0  
**Date**: November 16, 2025  
**Status**: ✅ Completed

---

## 🎯 Objectives

1. Transform the basic welcome page into a comprehensive analytics dashboard
2. Display key performance indicators (KPIs) with trend analysis
3. Integrate interactive charts for financial data visualization
4. Present real-time session information and user context
5. Provide auto-refresh capabilities for live data updates
6. Ensure full compatibility with existing architecture and services

---

## 🏗️ Architecture

### Component Structure

```
ui/
├── dashboard_window.py         # Main dashboard implementation
├── charts_utils.py             # Reusable chart components
├── layout_components.py        # Layout primitives (existing)
├── animations.py               # Animation utilities (existing)
└── base_ui.py                  # Base module interface (existing)

models/
├── pos.py                      # Sale, SaleLine, Payment models
└── ...                         # Other domain models

core/
└── database.py                 # Database connection
```

### Class Hierarchy

```
QWidget
└── ModuleWidget (base_ui.py)
    └── DashboardWindow (dashboard_window.py)
        ├── KPICard (custom Card subclass)
        └── ChartWidget (charts_utils.py)
```

---

## 📦 Implementation Details

### 1. Dashboard Window (`ui/dashboard_window.py`)

**Main Class**: `DashboardWindow`

**Inherits From**: `ModuleWidget` (provides session management, error handling, bilingual support)

**Key Features**:
- **Real-time KPI Cards**: 4 metric cards with trend indicators
  - Total Sales Today
  - Invoices Today
  - Active Customers
  - Average Invoice Value
- **Interactive Charts**: 3 chart visualizations
  - Sales Trend (7-day line chart)
  - Payment Methods (pie chart)
  - Top Products (bar chart)
- **Session Information**: User name, role, branch, timestamp
- **Auto-refresh**: Automatic data refresh every 5 minutes
- **Branch Filtering**: Respects user's branch assignment
- **Responsive Layout**: Scrollable grid layout adapts to content

**Data Flow**:
```
DashboardWindow
    ↓
load_data(session)
    ↓
├── _load_kpi_data(session)      → Database queries
├── _load_chart_data(session)    → Aggregated data
    ↓
├── _update_kpi_cards()          → UI update
└── _update_charts()             → Chart rendering
```

**Database Queries**:
- Aggregates sales by date (today vs yesterday for trends)
- Groups payments by method for distribution
- Ranks products by revenue (last 7 days)
- Counts active customers
- Calculates average invoice values

**Performance Considerations**:
- Uses `func.coalesce()` for safe aggregation
- Filters by `SaleStatus.POSTED` for accurate data
- Limits product query to top 5 items
- Caches data between UI updates

---

### 2. KPI Card Component

**Class**: `KPICard` (extends `Card`)

**Features**:
- Large value display (32pt bold font)
- Icon support (emoji or icon fonts)
- Trend indicators with color coding:
  - 🟢 Green (↑) for positive trends
  - 🔴 Red (↓) for negative trends
  - ⚪ Gray (→) for flat trends
- Bilingual labels
- Loading state support

**Signals**:
- `value_updated`: Emitted when value changes

**Usage**:
```python
kpi_card = KPICard(
    "Total Sales Today | إجمالي المبيعات اليوم",
    icon="💰",
    trend_enabled=True
)
kpi_card.set_value("$12,345.67", trend=15.3)
```

---

### 3. Charts Utilities Module (`ui/charts_utils.py`)

**Purpose**: Provides reusable, theme-aware chart components using matplotlib.

**Chart Types**:

#### Line Chart
```python
create_line_chart(
    data=[{'date': '11/15', 'value': 1250.50}, ...],
    x_key='date',
    y_key='value',
    title="Sales Trend",
    theme=ChartTheme.MODERN
)
```

**Features**:
- Line with area fill
- Data point markers
- Value labels (optional)
- Grid overlay

#### Bar Chart
```python
create_bar_chart(
    data=[{'product': 'Product A', 'sales': 5200}, ...],
    x_key='product',
    y_key='sales',
    title="Top Products"
)
```

**Features**:
- Vertical or horizontal bars
- Color gradient across bars
- Value labels on bars
- Rotated labels for readability

#### Pie Chart
```python
create_pie_chart(
    data=[{'method': 'CASH', 'total': 12500}, ...],
    label_key='method',
    value_key='total',
    title="Payment Methods"
)
```

**Features**:
- Percentage display
- Exploded largest slice
- Shadow effect
- Legend with labels

#### Area Chart
```python
create_area_chart(
    data=[{'date': '11/15', 'value': 1250}, ...],
    x_key='date',
    y_key='value',
    title="Cumulative Sales"
)
```

**Features**:
- Filled area with transparency
- Line overlay
- Support for stacked series

---

### 4. Theme Support

**Available Themes**:
- `ChartTheme.LIGHT`: Clean, bright colors
- `ChartTheme.DARK`: Dark mode compatible
- `ChartTheme.MODERN`: Gradient colors (default)
- `ChartTheme.PROFESSIONAL`: Corporate style

**Color Palettes**: Each theme includes:
- Primary, secondary, accent colors
- Warning and info colors
- Background and text colors
- Grid color
- Series colors (6-color palette for multiple data series)

**Theme Application**:
- Automatically styles axes, labels, titles
- Applies background colors
- Sets text colors for readability
- Configures grid appearance

---

## 🔧 Integration

### Module Registry Update

File: `ui/main_window.py`

```python
MODULE_REGISTRY = {
    "dashboard": ("ui.dashboard_window", "DashboardWindow", "dashboard.view"),
    # ... other modules
}
```

**Impact**: Dashboard is now loaded dynamically like other modules, with permission-based access.

### Permission Requirements

- **Permission Code**: `dashboard.view`
- **Default Access**: All users (typically granted to all roles)
- **Branch Filtering**: Automatic if user has assigned branch

---

## 📊 Data Models Used

### Sale Model
- `id`, `invoice_no`, `invoice_date`
- `grand_total`, `status`
- `branch_id`, `cashier_user_id`
- Relationships: `lines`, `payments`

### SaleLine Model
- `product_name`, `quantity`
- `line_total`, `unit_cost`

### Payment Model
- `method` (CASH, CARD, CREDIT)
- `amount`

### Customer Model
- `is_active`

---

## 🎨 UI/UX Features

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ Welcome Header (User Info + Session Data)               │
├─────────────────────────────────────────────────────────┤
│ 📊 Key Metrics                                          │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│ │ Total   │ │Invoices │ │Customers│ │Avg      │       │
│ │ Sales   │ │ Today   │ │ Active  │ │Invoice  │       │
│ │$12,345  │ │   42    │ │   156   │ │ $294.41 │       │
│ │ ↑ +15%  │ │ ↑ +8%   │ │         │ │         │       │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
├─────────────────────────────────────────────────────────┤
│ 📉 Analytics                                            │
│ ┌───────────────────────────────────────────────┐       │
│ │ Sales Trend (7 Days) - Line Chart             │       │
│ │ [Interactive matplotlib chart]                │       │
│ └───────────────────────────────────────────────┘       │
│ ┌───────────────────┐ ┌───────────────────────┐       │
│ │ Payment Methods   │ │ Top Products          │       │
│ │ [Pie Chart]       │ │ [Bar Chart]           │       │
│ └───────────────────┘ └───────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Animations

1. **Fade-in**: Main scroll area fades in on load
2. **Sequential Reveal**: KPI cards appear sequentially (80ms delay between each)
3. **Smooth Transitions**: Chart replacements use widget transitions

### Responsive Design

- **Scroll Area**: Entire dashboard is scrollable for smaller screens
- **Grid Layout**: Charts adapt to available space
- **Minimum Heights**: Cards have minimum heights to prevent collapse
- **Size Policies**: Widgets expand to fill available space

### Bilingual Support

All text elements support English | Arabic format:
- KPI card titles
- Chart titles
- Section headers
- Loading messages
- Error messages

---

## 🔄 Auto-Refresh System

**Refresh Interval**: 5 minutes (300,000 ms)

**Implementation**:
```python
self.auto_refresh_timer = QTimer(self)
self.auto_refresh_timer.timeout.connect(self.refresh_view)
self.auto_refresh_timer.start(300000)
```

**Cleanup**: Timer is stopped on window close to prevent memory leaks.

**Manual Refresh**: Users can navigate away and back to trigger refresh.

---

## 🛠️ Utility Functions

### Chart Utilities

**`format_currency(value, symbol="$")`**
- Formats large numbers with K/M suffixes
- Example: 1250000 → "$1.3M"

**`calculate_trend(current, previous)`**
- Returns percentage change and direction
- Returns: `(15.3, 'up')` or `(-8.2, 'down')`

**`aggregate_data(data, group_key, value_key, aggregation)`**
- Groups and aggregates data
- Supports: sum, avg, count, min, max

---

## 📈 Performance Optimization

### Database Queries

1. **Indexed Columns Used**:
   - `Sale.invoice_date` (Index: `idx_sales_invoice_date`)
   - `Sale.status` (Index: `idx_sales_status`)
   - `Sale.branch_id` (Index: `idx_sales_company_branch`)

2. **Query Optimization**:
   - Uses `func.date()` for date comparisons
   - Filters by status before aggregation
   - Limits results (top 5 products)
   - Uses `coalesce()` for null safety

3. **Caching**:
   - KPI data cached in `self._kpi_data`
   - Chart data cached in `self._chart_data`
   - Only refreshed on explicit refresh or timer

### Rendering Performance

1. **Chart Rendering**:
   - Matplotlib figures created once
   - Canvas redraws only on data change
   - Uses tight_layout() for optimization

2. **Widget Management**:
   - Old chart widgets properly deleted with `deleteLater()`
   - Prevents memory leaks from chart replacements

---

## 🧪 Testing Guidelines

### Manual Testing Checklist

- [ ] Dashboard loads without errors
- [ ] KPI cards display correct values
- [ ] Trend indicators show correct colors (up/down/flat)
- [ ] Sales trend chart displays 7 days of data
- [ ] Payment methods pie chart shows distribution
- [ ] Top products bar chart ranks correctly
- [ ] User session info displays (name, role, branch)
- [ ] Branch filtering works (user sees only their branch data)
- [ ] Auto-refresh updates data after 5 minutes
- [ ] Charts are theme-aware (match current theme)
- [ ] Bilingual labels display correctly
- [ ] Animations play smoothly on load
- [ ] Scroll area works for smaller screens
- [ ] No console errors or warnings

### Test with Sample Data

1. **Create Test Sales**:
```sql
-- Insert test sales for today
INSERT INTO sales (id, invoice_no, invoice_date, grand_total, status, branch_id, cashier_user_id, ...)
VALUES (gen_random_uuid(), 'INV-001', NOW(), 1250.50, 'POSTED', ...);
```

2. **Create Test Payments**:
```sql
INSERT INTO payments (id, sale_id, method, amount)
VALUES (gen_random_uuid(), <sale_id>, 'CASH', 800.00);
```

3. **Create Test Customers**:
```sql
INSERT INTO customers (id, name, is_active)
VALUES (gen_random_uuid(), 'Test Customer', true);
```

### Performance Testing

1. **Large Dataset**: Test with 1000+ sales records
2. **Branch Filtering**: Test with multiple branches
3. **Memory**: Monitor memory usage over multiple refreshes
4. **Render Time**: Measure chart rendering time

---

## 🐛 Troubleshooting

### Issue: Charts Not Displaying

**Cause**: Matplotlib backend issue or missing data

**Solution**:
1. Verify matplotlib installed: `pip install matplotlib`
2. Check backend: `matplotlib.use('Qt5Agg')`
3. Verify data is returned from queries
4. Check console for matplotlib errors

### Issue: No Data Displayed

**Cause**: No sales records or incorrect date filtering

**Solution**:
1. Verify sales exist with `SaleStatus.POSTED`
2. Check invoice_date is today
3. Verify user's branch_id matches sales
4. Check database connection

### Issue: Trend Percentages Incorrect

**Cause**: Division by zero or missing yesterday data

**Solution**:
1. Ensure comparison data exists (yesterday's sales)
2. Check zero-handling in `_load_kpi_data()`
3. Verify date filtering is correct

### Issue: Slow Loading

**Cause**: Large dataset or unoptimized queries

**Solution**:
1. Add database indexes (see Performance section)
2. Limit date range (currently 7 days)
3. Reduce chart data points
4. Enable query logging to identify slow queries

---

## 🔒 Security Considerations

### Permission-Based Access

- Dashboard requires `dashboard.view` permission
- Branch filtering ensures users see only their branch data
- No raw SQL queries (uses SQLAlchemy ORM)

### Data Exposure

- Only aggregated data displayed (no individual transaction details)
- Customer names not exposed on dashboard
- User can only see data from their assigned branch

---

## 🚀 Future Enhancements

### Phase F2.6 (Proposed)

1. **Enhanced Filters**:
   - Date range selector (week/month/year)
   - Branch selector for multi-branch users
   - Status filters (posted/pending/voided)

2. **Additional KPIs**:
   - Revenue vs Target
   - Top Customer
   - Low Stock Alerts
   - Pending Orders Count

3. **Advanced Charts**:
   - Comparative charts (this week vs last week)
   - Heatmap for sales by hour
   - Funnel chart for sales pipeline
   - Gauge charts for targets

4. **Export Capabilities**:
   - Export charts as PNG/PDF
   - Export data as Excel/CSV
   - Print dashboard report

5. **Real-Time Updates**:
   - WebSocket integration for live updates
   - Push notifications for milestones
   - Live sales counter

6. **Drill-Down**:
   - Click chart to see details
   - Filter other charts by selection
   - Navigate to related modules

---

## 📚 Code Examples

### Creating Custom KPI Card

```python
from ui.dashboard_window import KPICard

# Create card
card = KPICard(
    title="Custom Metric | مقياس مخصص",
    icon="📌",
    trend_enabled=True
)

# Update value
card.set_value("$1,234.56", trend=12.5)

# Connect signal
card.value_updated.connect(lambda val: print(f"New value: {val}"))
```

### Creating Custom Chart

```python
from ui.charts_utils import create_line_chart, ChartTheme

data = [
    {'month': 'Jan', 'revenue': 15000},
    {'month': 'Feb', 'revenue': 18500},
    {'month': 'Mar', 'revenue': 22000},
]

chart = create_line_chart(
    data=data,
    x_key='month',
    y_key='revenue',
    title="Monthly Revenue",
    x_label="Month",
    y_label="Revenue ($)",
    theme=ChartTheme.PROFESSIONAL,
    show_markers=True,
    show_values=True
)

# Add to layout
layout.addWidget(chart)
```

### Exporting Chart

```python
# Export chart to file
chart.export_to_file("sales_report.png", dpi=300)
```

### Custom Data Aggregation

```python
from ui.charts_utils import aggregate_data

sales_data = [
    {'product': 'A', 'amount': 100},
    {'product': 'A', 'amount': 150},
    {'product': 'B', 'amount': 200},
]

aggregated = aggregate_data(
    data=sales_data,
    group_key='product',
    value_key='amount',
    aggregation='sum'
)
# Result: [{'product': 'A', 'amount': 250}, {'product': 'B', 'amount': 200}]
```

---

## 📋 Dependencies

### Required Packages

```
PyQt6>=6.4.0              # GUI framework
matplotlib>=3.5.0         # Chart rendering
numpy>=1.21.0             # Numerical operations (matplotlib dependency)
SQLAlchemy>=2.0.0         # ORM and database
```

### Installation

```bash
pip install PyQt6 matplotlib numpy sqlalchemy
```

Or using the project's requirements:
```bash
pip install -r requirements.txt
```

---

## 🔗 Related Files

### Core Files
- `ui/dashboard_window.py` - Main dashboard implementation
- `ui/charts_utils.py` - Chart utilities and components
- `ui/base_ui.py` - Base module interface
- `ui/layout_components.py` - Layout primitives
- `ui/animations.py` - Animation utilities

### Model Files
- `models/pos.py` - Sale, SaleLine, Payment models
- `models/base.py` - Base model with timestamps
- `models/__init__.py` - Model exports

### Configuration
- `core/database.py` - Database connection
- `core/db_utils.py` - Database utilities
- `.env` - Environment configuration

---

## 📝 Changelog

### Version 1.0.0 (November 16, 2025)

**Added**:
- ✅ Modern dashboard with KPI cards
- ✅ Interactive charts (line, bar, pie)
- ✅ Real-time session information
- ✅ Auto-refresh every 5 minutes
- ✅ Branch-filtered data display
- ✅ Trend indicators with color coding
- ✅ Bilingual support throughout
- ✅ Theme-aware chart rendering
- ✅ Responsive scroll layout
- ✅ Smooth animations on load
- ✅ Chart export capabilities
- ✅ Comprehensive error handling
- ✅ Performance optimizations

**Modified**:
- Updated `MODULE_REGISTRY` to use `DashboardWindow`
- Enhanced main window to support dynamic dashboard loading

**Documentation**:
- Created comprehensive implementation documentation
- Added code examples and usage guidelines
- Included troubleshooting guide

---

## 👥 Credits

**Development Team**: Hassad ERP Development Team  
**Phase Lead**: Senior Python/PyQt6 Developer  
**Architecture**: F2.x Modernization Framework  
**Testing**: QA Team

---

## 📞 Support

For issues, questions, or enhancements:
1. Check this documentation first
2. Review troubleshooting section
3. Check logs: `logs/layout_engine.log`, `logs/ui_routing.log`
4. Contact development team

---

**End of Documentation**

*Last Updated: November 16, 2025*
*Phase: F2.5 - Dashboard Analytics Modernization*
*Status: ✅ Production Ready*
