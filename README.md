# Hassad ERP System - Phase 1

**Professional Offline-First Desktop POS & ERP Accounting System**

## Overview

Hassad System is a comprehensive, modular ERP and POS solution designed for offline-first operations with multi-branch support. This is **Phase 1** of a 6-phase development roadmap, focusing on foundational database architecture and project initialization.

### Phase 1 Deliverables
- ✅ Project structure and configuration
- ✅ Database schema with SQLAlchemy ORM
- ✅ Alembic migration system
- ✅ Core models: Company, Branch, User, Role, Permission, AuditLog, Settings
- ✅ Seed data scripts
- ✅ Testing framework
- ✅ Development utilities

### Phase 2 Deliverables (Accounting Engine)
- ✅ Chart of Accounts (COA) management
- ✅ Journal entries with double-entry validation
- ✅ Posting and reversal logic
- ✅ Trial balance calculation
- ✅ Accounting services and schemas

### Phase 3 Deliverables (Inventory Management)
- ✅ Product catalog with categories and units
- ✅ Batch tracking and expiry management
- ✅ Stock movements (IN, OUT, ADJUSTMENT, SALE, RETURN)
- ✅ Weighted Average Cost (WAC) calculation
- ✅ Inventory valuation and stock queries
- ✅ Integration with accounting

### Phase 4 Deliverables (Sales & POS)
- ✅ POS business logic with sales processing
- ✅ Multi-payment support (Cash, Card, Credit)
- ✅ Receipt rendering with Arabic RTL support
- ✅ ESC/POS thermal printer integration
- ✅ Barcode and QR code generation
- ✅ Returns and refunds processing
- ✅ PyQt6 desktop cashier interface
- ✅ Complete integration with Inventory and Accounting

### Phase 5 Deliverables (Purchases & Suppliers)
- ✅ Supplier management with catalog
- ✅ Purchase Order (PO) lifecycle with approval workflow
- ✅ Goods Receipt Notes (GRN) with inventory integration
- ✅ Purchase Invoices with 3-way matching (PO-GRN-Invoice)
- ✅ Approval workflow engine for POs and invoices
- ✅ Supplier payments with accounting integration
- ✅ Multi-supplier per product support
- ✅ Weighted Average Cost calculation on purchases
- ✅ Complete integration with Accounting and Inventory

### Future Phases
- **Phase 6**: Reporting & System Utilities

## Technology Stack

- **Python**: 3.11+
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validation**: Pydantic 2.0
- **Testing**: Pytest
- **Desktop UI**: PyQt6
- **Thermal Printing**: python-escpos
- **Barcode/QR**: python-barcode, qrcode
- **Image Processing**: Pillow

## Project Structure

\`\`\`
hassad/
├── core/               # Core configuration and utilities
│   ├── accounting/     # Phase 2: Accounting engine
│   ├── inventory/      # Phase 3: Inventory management
│   ├── pos/            # Phase 4: POS and sales
│   └── purchases/      # Phase 5: Purchases and suppliers
├── models/             # SQLAlchemy ORM models
│   ├── accounting.py   # Accounting models
│   ├── inventory.py    # Inventory models
│   ├── pos.py          # POS and sales models
│   └── purchases.py    # Purchases and suppliers models
├── integrations/       # External integrations
│   ├── escpos_adapter.py      # Thermal printer adapter
│   ├── barcode_adapter.py     # Barcode/QR generation
│   └── supplier_adapter.py    # Supplier system integrations
├── services/           # Business logic layer
├── api/                # API endpoints (future phases)
├── ui/                 # Desktop UI components
├── migrations/         # Alembic database migrations
├── scripts/            # Utility scripts
│   ├── seed_data.py                    # Phase 1 seed data
│   ├── seed_chart_of_accounts.py       # Phase 2 COA seed
│   ├── seed_inventory_data.py          # Phase 3 inventory seed
│   ├── seed_pos_data.py                # Phase 4 POS seed
│   └── seed_suppliers_and_purchases.py # Phase 5 purchases seed
├── tests/              # Test suite
└── docs/               # Documentation
\`\`\`

## Installation

### Prerequisites

1. **Python 3.11+**
   \`\`\`bash
   python --version  # Should be 3.11 or higher
   \`\`\`

2. **PostgreSQL 14+**
   \`\`\`bash
   psql --version
   \`\`\`

3. **Poetry** (recommended) or pip
   \`\`\`bash
   pip install poetry
   \`\`\`

### Setup Steps

1. **Clone or extract the project**
   \`\`\`bash
   cd hassad
   \`\`\`

2. **Create virtual environment**
   \`\`\`bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   \`\`\`

3. **Install dependencies**
   
   Using Poetry (recommended):
   \`\`\`bash
   poetry install
   \`\`\`
   
   Using pip:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Configure environment variables**
   \`\`\`bash
   cp .env.example .env
   # Edit .env with your database credentials
   \`\`\`

5. **Create PostgreSQL database**
   \`\`\`bash
   # On Windows (PowerShell)
   .\scripts\create_test_db.ps1
   
   # On macOS/Linux
   chmod +x scripts/create_test_db.sh
   ./scripts/create_test_db.sh
   \`\`\`
   
   Or manually:
   \`\`\`sql
   CREATE DATABASE hassad_erp;
   CREATE USER hassad_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE hassad_erp TO hassad_user;
   \`\`\`

6. **Run database migrations**
   \`\`\`bash
   # On Windows (PowerShell)
   .\scripts\run_migrations.ps1
   
   # On macOS/Linux
   chmod +x scripts/run_migrations.sh
   ./scripts/run_migrations.sh
   \`\`\`
   
   Or manually:
   \`\`\`bash
   alembic upgrade head
   \`\`\`

7. **Seed initial data**
   \`\`\`bash
   python scripts/seed_data.py
   \`\`\`

8. **Seed POS data (Phase 4)**
   \`\`\`bash
   python scripts/seed_pos_data.py
   \`\`\`

9. **Seed Purchases data (Phase 5)**
   \`\`\`bash
   python scripts/seed_suppliers_and_purchases.py
   \`\`\`

## Running the POS Application

### Desktop POS Interface

\`\`\`bash
# Run the PyQt6 POS application
python -m core.pos.ui

# Or create a launcher script
python scripts/launch_pos.py
\`\`\`

### POS Configuration

Configure POS settings in the database via `pos_settings` table or through the admin interface:

- **Stock Management**: Auto-deduct on sale or on post
- **Accounting**: Auto-post journals to accounting
- **Receipt Settings**: Paper width (58mm/80mm), header/footer text
- **Tax Settings**: Default VAT rate, tax-inclusive pricing
- **Payment Settings**: Allow partial payments, overpayments
- **Return Policy**: Allow returns, return window (days)
- **Printer**: Device path for thermal printer

### Receipt Printing

\`\`\`python
from core.pos.receipt import ReceiptRenderer
from integrations.escpos_adapter import EscposAdapter

# Render receipt
renderer = ReceiptRenderer(paper_width="80mm")
receipt_image = renderer.render_arabic_receipt_image(
    sale, lines, payments, company_info, totals
)

# Print to thermal printer
with EscposAdapter(printer_type="usb", vendor_id=0x04b8, product_id=0x0e15) as printer:
    printer.print_image(receipt_image)
    printer.cut_paper()
\`\`\`

### Barcode Scanning

The POS interface supports barcode scanning via:
- USB barcode scanners (keyboard emulation)
- Manual entry in search field (F2)
- Product quick keys

## Database Schema

### Core Tables

- **companies**: Multi-company support with legal and tax information
- **branches**: Branch/location management per company
- **users**: System users with authentication
- **roles**: Role-based access control
- **permissions**: Granular permission system
- **user_roles**: Many-to-many user-role mapping
- **role_permissions**: Many-to-many role-permission mapping
- **audit_logs**: Immutable audit trail
- **settings**: System and company-level configuration

### Key Features

- **UUID Primary Keys**: For distributed sync compatibility
- **UTC Timestamps**: All datetime fields use UTC
- **Soft Deletes**: Logical deletion with `deleted_at` field
- **Version Control**: Hash-based conflict detection
- **Audit Trail**: Comprehensive change tracking

## Development

### Running Tests

\`\`\`bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_database.py
\`\`\`

### Code Formatting

\`\`\`bash
# Format code with Black
black .

# Sort imports
isort .

# Lint with Flake8
flake8 .

# Type checking
mypy .
\`\`\`

Or use the utility script:
\`\`\`bash
# On Windows
.\scripts\format_and_lint.ps1

# On macOS/Linux
./scripts/format_and_lint.sh
\`\`\`

### Database Operations

\`\`\`bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
\`\`\`

## Configuration

Configuration is managed through environment variables and the `core/config.py` module using Pydantic Settings.

### Key Configuration Options

- **Database**: Connection parameters
- **Currency**: Default currency and decimal places
- **Rounding**: Rounding method for calculations
- **Posting Mode**: Manual or automatic transaction posting
- **Security**: Password policies and secret keys
- **Timezone**: Default timezone for operations

## Security Considerations

- ⚠️ **Never commit `.env` file** - Contains sensitive credentials
- ⚠️ **Change default SECRET_KEY** - Generate strong random key for production
- ⚠️ **Use strong passwords** - Enforce password policies
- ⚠️ **Audit logs are immutable** - Never delete or modify audit records
- ⚠️ **Database backups** - Implement regular backup strategy

## Testing

The test suite includes:

- Database connection tests
- Model validation tests
- Migration integrity tests
- Seed data verification tests
- **Phase 2**: Journal balancing, posting, trial balance
- **Phase 3**: Weighted average cost, stock movements, inventory valuation
- **Phase 4**: POS totals calculation, sale integration, receipt rendering, returns
- **Phase 5**: PO lifecycle, GRN and inventory integration, invoice posting, approval workflow

Run tests before committing changes:
\`\`\`bash
pytest -v

# Run specific phase tests
pytest tests/test_journal_balancing.py -v
pytest tests/test_weighted_average_cost.py -v
pytest tests/test_calc_totals.py -v
pytest tests/test_purchase_order_lifecycle.py -v
pytest tests/test_goods_receipt_and_inventory.py -v
pytest tests/test_purchase_invoice_posting.py -v
pytest tests/test_approval_workflow.py -v

# Run acceptance tests
pytest tests/acceptance_accounting_phase2.py -v
pytest tests/acceptance_inventory_phase3.py -v
pytest tests/acceptance_pos_phase4.py -v
pytest tests/acceptance_purchases_phase5.py -v
\`\`\`

## Troubleshooting

### Database Connection Issues

1. Verify PostgreSQL is running:
   \`\`\`bash
   # Windows
   pg_ctl status
   
   # macOS/Linux
   sudo systemctl status postgresql
   \`\`\`

2. Check `.env` credentials match your PostgreSQL setup

3. Ensure database exists:
   \`\`\`bash
   psql -U postgres -c "\l" | grep hassad_erp
   \`\`\`

### Migration Issues

1. Reset migrations (⚠️ destroys data):
   \`\`\`bash
   alembic downgrade base
   alembic upgrade head
   \`\`\`

2. Check migration history:
   \`\`\`bash
   alembic history
   alembic current
   \`\`\`

## Contributing

This is Phase 1 of a multi-phase project. Code should be:

- **Modular**: Easy to extend in future phases
- **Typed**: Use type hints throughout
- **Tested**: Write tests for new functionality
- **Documented**: Clear docstrings and comments
- **PEP8 Compliant**: Follow Python style guidelines

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.

---

**Version**: 0.5.0 (Phase 5 - Purchases Complete)  
**Last Updated**: 2025  
**Next Phase**: Reporting & System Utilities (Phase 6)
