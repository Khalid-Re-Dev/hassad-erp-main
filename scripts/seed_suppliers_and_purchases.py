"""
Seed script for Purchases & Suppliers module
Creates sample suppliers, purchase orders, and related data
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import uuid

from core.database import SessionLocal, engine
from models.company import Company
from models.branch import Branch
from models.user import User
from models.inventory import Product
from models.purchases import (
    Supplier, SupplierCatalog, PurchaseOrder, PurchaseOrderLine,
    POStatus
)


def seed_suppliers_and_purchases():
    """Seed suppliers and purchase orders"""
    session: Session = SessionLocal()
    
    try:
        print("Starting Purchases & Suppliers seed...")
        
        # Get first company and branch
        company = session.query(Company).first()
        if not company:
            print("Error: No company found. Run Phase 1 seed first.")
            return
        
        branch = session.query(Branch).filter(Branch.company_id == company.id).first()
        if not branch:
            print("Error: No branch found. Run Phase 1 seed first.")
            return
        
        # Get first user (admin)
        user = session.query(User).filter(User.company_id == company.id).first()
        if not user:
            print("Error: No user found. Run Phase 1 seed first.")
            return
        
        # Create suppliers
        suppliers_data = [
            {
                "name": "ABC Trading Co.",
                "tax_id": "300123456700003",
                "contact_name": "Ahmed Ali",
                "email": "ahmed@abctrading.com",
                "phone": "+966501234567",
                "address": "123 King Fahd Road, Riyadh, Saudi Arabia",
                "default_payment_terms": Decimal("30"),
            },
            {
                "name": "Global Supplies Ltd",
                "tax_id": "300987654300003",
                "contact_name": "Mohammed Hassan",
                "email": "mohammed@globalsupplies.com",
                "phone": "+966509876543",
                "address": "456 Prince Sultan Street, Jeddah, Saudi Arabia",
                "default_payment_terms": Decimal("45"),
            },
            {
                "name": "Premium Goods LLC",
                "tax_id": "300555666700003",
                "contact_name": "Fatima Ibrahim",
                "email": "fatima@premiumgoods.com",
                "phone": "+966505556667",
                "address": "789 Olaya Street, Riyadh, Saudi Arabia",
                "default_payment_terms": Decimal("60"),
            },
        ]
        
        suppliers = []
        for supplier_data in suppliers_data:
            supplier = Supplier(
                id=uuid.uuid4(),
                company_id=company.id,
                **supplier_data,
                is_active=True
            )
            session.add(supplier)
            suppliers.append(supplier)
        
        session.flush()
        print(f"Created {len(suppliers)} suppliers")
        
        # Get products for catalog
        products = session.query(Product).filter(Product.company_id == company.id).limit(10).all()
        
        if products:
            # Add products to supplier catalogs
            for i, supplier in enumerate(suppliers):
                # Each supplier has 3-5 products
                supplier_products = products[i*3:(i+1)*5]
                for product in supplier_products:
                    catalog_item = SupplierCatalog(
                        id=uuid.uuid4(),
                        supplier_id=supplier.id,
                        product_id=product.id,
                        supplier_sku=f"SUP-{supplier.name[:3].upper()}-{product.sku}",
                        lead_time_days=Decimal(str(7 + i * 3)),
                        purchase_price=Decimal("20.00") + Decimal(str(i * 5)),
                        min_order_qty=Decimal("10"),
                        is_preferred=(i == 0),
                        is_active=True
                    )
                    session.add(catalog_item)
            
            session.flush()
            print("Created supplier catalog items")
        
        # Create sample purchase orders
        po_data = [
            {
                "supplier": suppliers[0],
                "status": POStatus.DRAFT,
                "products": products[:3] if len(products) >= 3 else products,
            },
            {
                "supplier": suppliers[1],
                "status": POStatus.SUBMITTED,
                "products": products[3:6] if len(products) >= 6 else products,
            },
            {
                "supplier": suppliers[2],
                "status": POStatus.APPROVED,
                "products": products[6:9] if len(products) >= 9 else products,
            },
        ]
        
        for i, po_info in enumerate(po_data):
            # Generate PO number
            year = datetime.now(timezone.utc).year
            po_number = f"PO-{year}-{i+1:04d}"
            
            # Calculate totals
            subtotal = Decimal("0")
            tax_total = Decimal("0")
            
            po = PurchaseOrder(
                id=uuid.uuid4(),
                company_id=company.id,
                branch_id=branch.id,
                supplier_id=po_info["supplier"].id,
                po_number=po_number,
                status=po_info["status"],
                order_date=datetime.now(timezone.utc) - timedelta(days=i*5),
                expected_delivery_date=datetime.now(timezone.utc) + timedelta(days=14),
                created_by=user.id,
                notes=f"Sample PO {i+1} for testing"
            )
            
            if po_info["status"] == POStatus.APPROVED:
                po.approved_by = user.id
                po.approved_at = datetime.now(timezone.utc) - timedelta(days=i*3)
            
            session.add(po)
            session.flush()
            
            # Add PO lines
            for j, product in enumerate(po_info["products"]):
                ordered_qty = Decimal("50") + Decimal(str(j * 10))
                unit_price = Decimal("25.00") + Decimal(str(j * 5))
                tax_rate = Decimal("15")
                
                line_subtotal = (ordered_qty * unit_price).quantize(Decimal("0.01"))
                line_tax = (line_subtotal * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
                line_total = line_subtotal + line_tax
                
                po_line = PurchaseOrderLine(
                    id=uuid.uuid4(),
                    purchase_order_id=po.id,
                    product_id=product.id,
                    description=product.name_en,
                    ordered_qty=ordered_qty,
                    received_qty=Decimal("0"),
                    unit_price=unit_price,
                    tax_rate=tax_rate,
                    line_subtotal=line_subtotal,
                    line_tax=line_tax,
                    line_total=line_total,
                    expected_delivery_date=po.expected_delivery_date
                )
                session.add(po_line)
                
                subtotal += line_subtotal
                tax_total += line_tax
            
            # Update PO totals
            po.subtotal = subtotal
            po.tax_total = tax_total
            po.total_amount = subtotal + tax_total
        
        session.commit()
        print(f"Created {len(po_data)} purchase orders with lines")
        
        print("\n✅ Purchases & Suppliers seed completed successfully!")
        print(f"   - {len(suppliers)} suppliers")
        print(f"   - {len(po_data)} purchase orders")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error during seed: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_suppliers_and_purchases()
