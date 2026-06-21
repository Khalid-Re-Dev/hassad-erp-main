"""
Branch synchronization service for offline-first data exchange.
"""

import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.inventory import Product, StockMovement
from models.pos import Sale, SaleLine
from models.accounting import JournalEntry, JournalLine
from models.purchases import PurchaseOrder, PurchaseInvoice
from .conflict_resolver import ConflictResolver, ConflictResolutionStrategy


class SyncError(Exception):
    """Raised when sync operations fail."""
    pass


class SyncService:
    """
    Service for branch-to-branch data synchronization.
    
    Supports:
    - Export of transactional data to JSON envelope
    - Import with conflict detection
    - HMAC signatures for integrity
    - Configurable sync scope
    """

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or 'SYNC_SECRET_PLACEHOLDER'
        self.conflict_resolver = ConflictResolver()

    def export_sync_data(
        self,
        session: Session,
        company_id: UUID,
        branch_id: UUID,
        since_date: Optional[datetime] = None,
        include_products: bool = True,
        include_sales: bool = True,
        include_purchases: bool = True,
        include_journals: bool = True
    ) -> Dict[str, Any]:
        """
        Export sync data for a branch.
        
        Args:
            session: Database session
            company_id: Company ID
            branch_id: Branch ID
            since_date: Only export data modified after this date
            include_*: Flags for what data to include
            
        Returns:
            Sync envelope dictionary
        """
        envelope = {
            'meta': {
                'file_uuid': str(uuid4()),
                'company_id': str(company_id),
                'branch_id': str(branch_id),
                'generated_at_utc': datetime.utcnow().isoformat(),
                'version': 1,
                'tool_version': 'Hassad v0.1',
                'since_date': since_date.isoformat() if since_date else None
            },
            'data': {},
            'conflicts': [],
            'signature': None
        }
        
        # Export products
        if include_products:
            products = self._export_products(session, company_id, since_date)
            envelope['data']['products'] = products
        
        # Export sales
        if include_sales:
            sales = self._export_sales(session, company_id, branch_id, since_date)
            envelope['data']['sales'] = sales
        
        # Export purchases
        if include_purchases:
            purchases = self._export_purchases(session, company_id, branch_id, since_date)
            envelope['data']['purchases'] = purchases
        
        # Export journal entries
        if include_journals:
            journals = self._export_journals(session, company_id, branch_id, since_date)
            envelope['data']['journal_entries'] = journals
        
        # Export stock movements
        stock_movements = self._export_stock_movements(session, company_id, branch_id, since_date)
        envelope['data']['stock_movements'] = stock_movements
        
        # Generate signature
        envelope['signature'] = self._generate_signature(envelope)
        
        return envelope

    def import_sync_data(
        self,
        session: Session,
        envelope: Dict[str, Any],
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LATEST_WINS,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Import sync data from envelope.
        
        Args:
            session: Database session
            envelope: Sync envelope dictionary
            strategy: Conflict resolution strategy
            dry_run: If True, detect conflicts without importing
            
        Returns:
            Import results with conflicts detected
            
        Raises:
            SyncError: If signature invalid or import fails
        """
        # Verify signature
        if not self._verify_signature(envelope):
            raise SyncError("Invalid signature - data may be tampered")
        
        results = {
            'imported': {
                'products': 0,
                'sales': 0,
                'purchases': 0,
                'journals': 0,
                'stock_movements': 0
            },
            'conflicts': [],
            'errors': []
        }
        
        if dry_run:
            # Only detect conflicts
            conflicts = self._detect_conflicts(session, envelope, strategy)
            results['conflicts'] = conflicts
            return results
        
        # Import data with conflict resolution
        try:
            # Import products
            if 'products' in envelope['data']:
                count, conflicts = self._import_products(
                    session, envelope['data']['products'], strategy
                )
                results['imported']['products'] = count
                results['conflicts'].extend(conflicts)
            
            # Import sales
            if 'sales' in envelope['data']:
                count, conflicts = self._import_sales(
                    session, envelope['data']['sales'], strategy
                )
                results['imported']['sales'] = count
                results['conflicts'].extend(conflicts)
            
            # Import purchases
            if 'purchases' in envelope['data']:
                count, conflicts = self._import_purchases(
                    session, envelope['data']['purchases'], strategy
                )
                results['imported']['purchases'] = count
                results['conflicts'].extend(conflicts)
            
            # Import journals
            if 'journal_entries' in envelope['data']:
                count, conflicts = self._import_journals(
                    session, envelope['data']['journal_entries'], strategy
                )
                results['imported']['journals'] = count
                results['conflicts'].extend(conflicts)
            
            # Import stock movements
            if 'stock_movements' in envelope['data']:
                count, conflicts = self._import_stock_movements(
                    session, envelope['data']['stock_movements'], strategy
                )
                results['imported']['stock_movements'] = count
                results['conflicts'].extend(conflicts)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise SyncError(f"Import failed: {e}")
        
        return results

    def save_envelope_to_file(self, envelope: Dict[str, Any], filepath: str):
        """Save sync envelope to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False, default=str)

    def load_envelope_from_file(self, filepath: str) -> Dict[str, Any]:
        """Load sync envelope from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _export_products(
        self,
        session: Session,
        company_id: UUID,
        since_date: Optional[datetime]
    ) -> List[Dict]:
        """Export products."""
        query = session.query(Product).filter(
            Product.company_id == company_id,
            Product.deleted_at.is_(None)
        )
        
        if since_date:
            query = query.filter(Product.updated_at >= since_date)
        
        products = query.all()
        
        return [
            {
                'id': str(p.id),
                'sku': p.sku,
                'barcode': p.barcode,
                'name_en': p.name_en,
                'name_ar': p.name_ar,
                'category_id': str(p.category_id) if p.category_id else None,
                'updated_at': p.updated_at.isoformat(),
                'version_hash': p.version_hash
            }
            for p in products
        ]

    def _export_sales(
        self,
        session: Session,
        company_id: UUID,
        branch_id: UUID,
        since_date: Optional[datetime]
    ) -> List[Dict]:
        """Export sales."""
        query = session.query(Sale).filter(
            Sale.company_id == company_id,
            Sale.branch_id == branch_id
        )
        
        if since_date:
            query = query.filter(Sale.created_at >= since_date)
        
        sales = query.all()
        
        return [
            {
                'id': str(s.id),
                'invoice_no': s.invoice_no,
                'total_amount': str(s.total_amount),
                'tax_total': str(s.tax_total),
                'created_at': s.created_at.isoformat(),
                'lines': [
                    {
                        'product_id': str(line.product_id),
                        'quantity': str(line.quantity),
                        'unit_price': str(line.unit_price),
                        'line_total': str(line.line_total)
                    }
                    for line in s.lines
                ]
            }
            for s in sales
        ]

    def _export_purchases(
        self,
        session: Session,
        company_id: UUID,
        branch_id: UUID,
        since_date: Optional[datetime]
    ) -> List[Dict]:
        """Export purchase invoices."""
        query = session.query(PurchaseInvoice).filter(
            PurchaseInvoice.company_id == company_id,
            PurchaseInvoice.branch_id == branch_id
        )
        
        if since_date:
            query = query.filter(PurchaseInvoice.created_at >= since_date)
        
        invoices = query.all()
        
        return [
            {
                'id': str(inv.id),
                'invoice_number': inv.invoice_number,
                'supplier_id': str(inv.supplier_id),
                'total_amount': str(inv.total_amount),
                'created_at': inv.created_at.isoformat()
            }
            for inv in invoices
        ]

    def _export_journals(
        self,
        session: Session,
        company_id: UUID,
        branch_id: UUID,
        since_date: Optional[datetime]
    ) -> List[Dict]:
        """Export journal entries."""
        query = session.query(JournalEntry).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.branch_id == branch_id,
            JournalEntry.posted == True
        )
        
        if since_date:
            query = query.filter(JournalEntry.created_at >= since_date)
        
        journals = query.all()
        
        return [
            {
                'id': str(j.id),
                'reference': j.reference,
                'entry_date': j.entry_date.isoformat(),
                'posted': j.posted,
                'lines': [
                    {
                        'account_id': str(line.account_id),
                        'debit': str(line.debit),
                        'credit': str(line.credit),
                        'description': line.description
                    }
                    for line in j.lines
                ]
            }
            for j in journals
        ]

    def _export_stock_movements(
        self,
        session: Session,
        company_id: UUID,
        branch_id: UUID,
        since_date: Optional[datetime]
    ) -> List[Dict]:
        """Export stock movements."""
        query = session.query(StockMovement).join(
            StockMovement.product
        ).filter(
            Product.company_id == company_id,
            StockMovement.branch_id == branch_id
        )
        
        if since_date:
            query = query.filter(StockMovement.created_at >= since_date)
        
        movements = query.all()
        
        return [
            {
                'id': str(m.id),
                'product_id': str(m.product_id),
                'movement_type': m.movement_type,
                'quantity': str(m.quantity),
                'unit_cost': str(m.unit_cost),
                'created_at': m.created_at.isoformat()
            }
            for m in movements
        ]

    def _import_products(
        self,
        session: Session,
        products: List[Dict],
        strategy: ConflictResolutionStrategy
    ) -> tuple[int, List[Dict]]:
        """Import products with conflict resolution."""
        imported = 0
        conflicts = []
        
        for product_data in products:
            product_id = UUID(product_data['id'])
            existing = session.query(Product).filter(Product.id == product_id).first()
            
            if existing:
                # Check for conflict
                if existing.version_hash != product_data.get('version_hash'):
                    conflict = {
                        'entity_type': 'product',
                        'entity_id': str(product_id),
                        'field': 'version_hash',
                        'local_value': existing.version_hash,
                        'remote_value': product_data.get('version_hash')
                    }
                    conflicts.append(conflict)
                    
                    # Apply strategy
                    if strategy == ConflictResolutionStrategy.LATEST_WINS:
                        # Update if remote is newer
                        remote_updated = datetime.fromisoformat(product_data['updated_at'])
                        if remote_updated > existing.updated_at:
                            self._update_product(existing, product_data)
                            imported += 1
                    elif strategy == ConflictResolutionStrategy.LOCAL_WINS:
                        # Keep local, skip import
                        pass
                    elif strategy == ConflictResolutionStrategy.MANUAL:
                        # Mark for manual resolution
                        conflict['requires_manual_resolution'] = True
            else:
                # New product, insert
                new_product = Product(
                    id=product_id,
                    sku=product_data['sku'],
                    barcode=product_data.get('barcode'),
                    name_en=product_data['name_en'],
                    name_ar=product_data['name_ar']
                )
                session.add(new_product)
                imported += 1
        
        return imported, conflicts

    def _import_sales(self, session: Session, sales: List[Dict], strategy) -> tuple[int, List[Dict]]:
        """Import sales (placeholder)."""
        # Similar logic to products
        return 0, []

    def _import_purchases(self, session: Session, purchases: List[Dict], strategy) -> tuple[int, List[Dict]]:
        """Import purchases (placeholder)."""
        return 0, []

    def _import_journals(self, session: Session, journals: List[Dict], strategy) -> tuple[int, List[Dict]]:
        """Import journals (placeholder)."""
        return 0, []

    def _import_stock_movements(self, session: Session, movements: List[Dict], strategy) -> tuple[int, List[Dict]]:
        """Import stock movements (placeholder)."""
        return 0, []

    def _update_product(self, product: Product, data: Dict):
        """Update product from sync data."""
        product.name_en = data['name_en']
        product.name_ar = data['name_ar']
        product.barcode = data.get('barcode')
        product.updated_at = datetime.utcnow()

    def _detect_conflicts(
        self,
        session: Session,
        envelope: Dict[str, Any],
        strategy: ConflictResolutionStrategy
    ) -> List[Dict]:
        """Detect conflicts without importing."""
        conflicts = []
        
        # Check products for conflicts
        if 'products' in envelope['data']:
            for product_data in envelope['data']['products']:
                product_id = UUID(product_data['id'])
                existing = session.query(Product).filter(Product.id == product_id).first()
                
                if existing and existing.version_hash != product_data.get('version_hash'):
                    conflicts.append({
                        'entity_type': 'product',
                        'entity_id': str(product_id),
                        'local_version': existing.version_hash,
                        'remote_version': product_data.get('version_hash')
                    })
        
        return conflicts

    def _generate_signature(self, envelope: Dict[str, Any]) -> str:
        """Generate HMAC signature for envelope."""
        # Create a copy without signature field
        data_to_sign = {
            'meta': envelope['meta'],
            'data': envelope['data']
        }
        
        message = json.dumps(data_to_sign, sort_keys=True, default=str).encode()
        signature = hmac.new(
            self.secret_key.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        
        return signature

    def _verify_signature(self, envelope: Dict[str, Any]) -> bool:
        """Verify HMAC signature of envelope."""
        provided_signature = envelope.get('signature')
        
        if not provided_signature:
            return False
        
        # Recalculate signature
        expected_signature = self._generate_signature(envelope)
        
        return hmac.compare_digest(provided_signature, expected_signature)


# Convenience functions

def export_sync_data(
    session: Session,
    company_id: UUID,
    branch_id: UUID,
    output_file: str,
    since_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Export sync data to file.
    
    Example:
        >>> from services.sync import export_sync_data
        >>> from datetime import datetime, timedelta
        >>> result = export_sync_data(
        ...     session,
        ...     company_id=company_id,
        ...     branch_id=branch_id,
        ...     output_file='sync_export_branch1.json',
        ...     since_date=datetime.now() - timedelta(days=7)
        ... )
    """
    service = SyncService()
    envelope = service.export_sync_data(
        session, company_id, branch_id, since_date=since_date
    )
    service.save_envelope_to_file(envelope, output_file)
    return envelope['meta']


def import_sync_data(
    session: Session,
    input_file: str,
    strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LATEST_WINS,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Import sync data from file.
    
    Example:
        >>> from services.sync import import_sync_data, ConflictResolutionStrategy
        >>> result = import_sync_data(
        ...     session,
        ...     input_file='sync_export_branch1.json',
        ...     strategy=ConflictResolutionStrategy.LATEST_WINS,
        ...     dry_run=True  # Check conflicts first
        ... )
        >>> print(f"Conflicts: {len(result['conflicts'])}")
    """
    service = SyncService()
    envelope = service.load_envelope_from_file(input_file)
    return service.import_sync_data(session, envelope, strategy, dry_run)


def create_sync_envelope(
    session: Session,
    company_id: UUID,
    branch_id: UUID,
    since_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Create sync envelope without saving to file."""
    service = SyncService()
    return service.export_sync_data(session, company_id, branch_id, since_date)
