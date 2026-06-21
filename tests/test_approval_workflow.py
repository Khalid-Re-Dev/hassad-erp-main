"""
Tests for Approval Workflow
Tests approval request creation and processing
"""
import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from core.purchases.services import (
    create_approval_request,
    act_on_approval,
    submit_purchase_order,
)
from core.purchases.schemas import ApprovalRequestCreate, ApprovalActionSchema
from models.purchases import ApprovalStatus


def test_create_approval_request(db_session: Session, test_company, test_branch, test_user, test_purchase_order):
    """Test creating an approval request"""
    # Arrange
    approval_dto = ApprovalRequestCreate(
        company_id=test_company.id,
        branch_id=test_branch.id,
        entity_type="PO",
        entity_id=test_purchase_order.id,
        requested_by=test_user.id,
        amount=test_purchase_order.total_amount,
        request_notes="Please approve this PO"
    )
    
    # Act
    approval = create_approval_request(db_session, approval_dto)
    
    # Assert
    assert approval.id is not None
    assert approval.status == ApprovalStatus.PENDING
    assert approval.entity_type == "PO"
    assert approval.entity_id == test_purchase_order.id


def test_approve_approval_request(db_session: Session, test_user, test_purchase_order):
    """Test approving an approval request"""
    # Arrange - submit PO to create approval request
    submit_purchase_order(db_session, test_purchase_order.id, test_user.id, require_approval=True)
    
    from models.purchases import ApprovalRequest
    approval = db_session.query(ApprovalRequest).filter(
        ApprovalRequest.entity_id == test_purchase_order.id
    ).first()
    
    action_dto = ApprovalActionSchema(
        approval_id=approval.id,
        approver_id=test_user.id,
        action="APPROVE",
        approval_notes="Approved for testing"
    )
    
    # Act
    result = act_on_approval(db_session, action_dto)
    
    # Assert
    assert result.status == ApprovalStatus.APPROVED
    assert result.approver_id == test_user.id
    assert result.acted_at is not None


def test_reject_approval_request(db_session: Session, test_user, test_purchase_order):
    """Test rejecting an approval request"""
    # Arrange - submit PO to create approval request
    submit_purchase_order(db_session, test_purchase_order.id, test_user.id, require_approval=True)
    
    from models.purchases import ApprovalRequest
    approval = db_session.query(ApprovalRequest).filter(
        ApprovalRequest.entity_id == test_purchase_order.id
    ).first()
    
    action_dto = ApprovalActionSchema(
        approval_id=approval.id,
        approver_id=test_user.id,
        action="REJECT",
        approval_notes="Insufficient budget"
    )
    
    # Act
    result = act_on_approval(db_session, action_dto)
    
    # Assert
    assert result.status == ApprovalStatus.REJECTED
    assert result.approval_notes == "Insufficient budget"


def test_cannot_act_on_already_processed_approval(db_session: Session, test_user, test_purchase_order):
    """Test that already processed approval cannot be acted on again"""
    # Arrange - submit and approve
    submit_purchase_order(db_session, test_purchase_order.id, test_user.id, require_approval=True)
    
    from models.purchases import ApprovalRequest
    approval = db_session.query(ApprovalRequest).filter(
        ApprovalRequest.entity_id == test_purchase_order.id
    ).first()
    
    action_dto = ApprovalActionSchema(
        approval_id=approval.id,
        approver_id=test_user.id,
        action="APPROVE"
    )
    
    act_on_approval(db_session, action_dto)
    
    # Act & Assert - try to act again
    from core.purchases.exceptions import PurchaseError
    with pytest.raises(PurchaseError, match="already"):
        act_on_approval(db_session, action_dto)
