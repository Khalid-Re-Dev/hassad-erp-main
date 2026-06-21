"""
Seed POS test data
Creates sample customers, POS settings, and test products with stock
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
import uuid

from core.database import SessionLocal
from models.pos import Customer, POSSettings
from models.inventory import Product, Category, Unit, StockMovement, MovementType
from models.accounting import Account, AccountType


def seed_pos_data():
    """Seed POS test data"""
    session = SessionLocal()
    
    try:
        print("Seeding POS data...")
        
        # Get first company and branch (from Phase 1 seed)
        from models.company import Company
        from models.branch import Branch
        company = session.query(Company).first()
        branch = session.query(Branch).first()
        
        if not company or not branch:
            print("Error: No company or branch found. Run seed_data.py first.")
            return
        
        print(f"Using company: {company.name}, branch: {branch.name}")
        
        # Create accounts for POS (if not exist)
        accounts_to_create = [
            ("1010", "Cash", AccountType.ASSET),
            ("1020", "Bank - Card Payments", AccountType.ASSET),
            ("1200", "Accounts Receivable", AccountType.ASSET),
            ("1300", "Inventory", AccountType.ASSET),
            ("2100", "VAT Payable", AccountType.LIABILITY),
            ("4000", "Sales Revenue", AccountType.REVENUE),
            ("5000", "Cost of Goods Sold", AccountType.EXPENSE),
        ]
        
        account_map = {}
        for code, name, acc_type in accounts_to_create:
            account = session.query(Account).filter(
                Account.company_id == company.id,
                Account.code == code
            ).first()
            
            if not account:
                account = Account(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    code=code,
                    name_en=name,
                    name_ar=name,  # Simplified
                    account_type=acc_type,
                    is_active=True,
                )
                session.add(account)
                print(f"Created account: {code} - {name}")
            
            account_map[code] = account
        
        session.flush()
        
        # Create POS settings
        pos_settings = session.query(POSSettings).filter(
            POSSettings.branch_id == branch.id
        ).first()
        
        if not pos_settings:
            pos_settings = POSSettings(
                id=uuid.uuid4(),
                company_id=company.id,
                branch_id=branch.id,
                auto_stock_deduct=True,
                allow_negative_stock=False,
                auto_post_journal=False,
                default_cash_account_id=account_map["1010"].id,
                default_card_account_id=account_map["1020"].id,
                default_receivable_account_id=account_map["1200"].id,
                default_revenue_account_id=account_map["4000"].id,
                default_vat_account_id=account_map["2100"].id,
                default_cogs_account_id=account_map["5000"].id,
                default_inventory_account_id=account_map["1300"].id,
                receipt_paper_width="80mm",
                default_tax_rate=Decimal('15.00'),
                tax_inclusive=False,
                allow_partial_payment=False,
                allow_overpayment=True,
                allow_returns=True,
                return_window_days=30,
            )
            session.add(pos_settings)
            print(f"Created POS settings for branch: {branch.name}")
        
        # Create sample customers
        customers_data = [
            ("CUST-001", "Walk-in Customer", "عميل عابر"),
            ("CUST-002", "Ahmed Ali", "أحمد علي"),
            ("CUST-003", "Sara Mohammed", "سارة محمد"),
        ]
        
        for code, name, name_ar in customers_data:
            customer = session.query(Customer).filter(
                Customer.company_id == company.id,
                Customer.code == code
            ).first()
            
            if not customer:
                customer = Customer(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    code=code,
                    name=name,
                    name_ar=name_ar,
                    credit_limit=Decimal('10000.00'),
                    is_active=True,
                )
                session.add(customer)
                print(f"Created customer: {code} - {name}")
        
        # Create sample products with stock
        category = session.query(Category).first()
        unit = session.query(Unit).first()
        
        if not category:
            category = Category(
                id=uuid.uuid4(),
                company_id=company.id,
                name_en="General",
                name_ar="عام",
            )
            session.add(category)
            session.flush()
        
        if not unit:
            unit = Unit(
                id=uuid.uuid4(),
                company_id=company.id,
                name="Piece",
                symbol="PC",
                conversion_to_base=Decimal('1.0000'),
            )
            session.add(unit)
            session.flush()
        
        products_data = [
            ("PROD-001", "1234567890123", "Product A", "منتج أ", Decimal('50.00'), Decimal('100.00')),
            ("PROD-002", "1234567890124", "Product B", "منتج ب", Decimal('30.00'), Decimal('60.00')),
            ("PROD-003", "1234567890125", "Product C", "منتج ج", Decimal('75.00'), Decimal('150.00')),
        ]
        
        for sku, barcode, name_en, name_ar, cost, price in products_data:
            product = session.query(Product).filter(
                Product.company_id == company.id,
                Product.sku == sku
            ).first()
            
            if not product:
                product = Product(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    sku=sku,
                    barcode=barcode,
                    name_en=name_en,
                    name_ar=name_ar,
                    category_id=category.id,
                    base_unit_id=unit.id,
                    track_batches=False,
                    track_expiry=False,
                    default_sales_account_id=account_map["4000"].id,
                    default_stock_account_id=account_map["1300"].id,
                    is_active=True,
                )
                session.add(product)
                session.flush()
                
                # Add initial stock
                stock_movement = StockMovement(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    branch_id=branch.id,
                    movement_type=MovementType.IN,
                    quantity=Decimal('100.0000'),
                    unit_cost=cost,
                    total_cost=Decimal('100.0000') * cost,
                    reference_type="INITIAL",
                    reference_id=uuid.uuid4(),
                )
                session.add(stock_movement)
                
                print(f"Created product: {sku} - {name_en} with stock: 100")
        
        session.commit()
        print("\nPOS data seeded successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding POS data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_pos_data()
