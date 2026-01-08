"""Fix SalesOrder column names - correct spelling mistakes

Revision ID: 002_fix_salesorder
Revises: 001_initial
Create Date: 2025-12-10

This migration fixes spelling errors in the SalesOrder table:
- Descount -> Discount (drop old column if both exist)
- BusinnesPartner_IdBusinnesPartner -> BusinessPartnerId
- Company_IdCompany -> CompanyId
- Company_PaymentMethod_IdCompany_PaymentMethod -> PaymentMethodId
- Company_PaymentTerm_IdCompany_PaymentTerm -> PaymentTermId
- Company_Utilization_IdCompany_Utilization -> UtilizationId
- Company_Branch_IdCompany_Branch -> BranchId
- Company_Freight_IdCompany_Freight -> FreightId
- SalesOrder_Redespacho_IdSalesOrder_Redespacho -> RedespachoSalesOrderId
- SincronizationStatus_IdSincronizationStatus -> SynchronizationStatusId
- Drop unused column: SalesOrder_IdSalesOrder
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '002_fix_salesorder'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_existing_columns():
    """Get list of existing column names in SalesOrder table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return [col['name'] for col in inspector.get_columns('SalesOrder')]


def upgrade() -> None:
    """
    Rename columns in SalesOrder table to fix spelling mistakes and simplify names.
    """
    existing_cols = get_existing_columns()
    
    # MySQL/MariaDB syntax - use CHANGE COLUMN for rename, DROP for removal
    
    # Handle Descount/Discount situation
    # If both exist, drop the old one. If only Descount exists, rename it.
    if 'Descount' in existing_cols and 'Discount' in existing_cols:
        # Both exist - drop the old one (data should already be in Discount)
        op.drop_column('SalesOrder', 'Descount')
    elif 'Descount' in existing_cols and 'Discount' not in existing_cols:
        # Only old column exists - rename it
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `Descount` `Discount` DECIMAL(13,2) NULL')
    
    # Fix spelling: BusinnesPartner -> BusinessPartner (simplified)
    if 'BusinnesPartner_IdBusinnesPartner' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `BusinnesPartner_IdBusinnesPartner` `BusinessPartnerId` INT NULL')
    
    # Simplify column names
    if 'Company_IdCompany' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `Company_IdCompany` `CompanyId` INT NULL')
    
    if 'Company_PaymentMethod_IdCompany_PaymentMethod' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `Company_PaymentMethod_IdCompany_PaymentMethod` `PaymentMethodId` INT NULL')
    
    if 'Company_PaymentTerm_IdCompany_PaymentTerm' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `Company_PaymentTerm_IdCompany_PaymentTerm` `PaymentTermId` INT NULL')
    
    if 'Company_Utilization_IdCompany_Utilization' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `Company_Utilization_IdCompany_Utilization` `UtilizationId` INT NULL')
    
    if 'Company_Branch_IdCompany_Branch' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `Company_Branch_IdCompany_Branch` `BranchId` INT NULL')
    
    if 'Company_Freight_IdCompany_Freight' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `Company_Freight_IdCompany_Freight` `FreightId` INT NULL')
    
    if 'SalesOrder_Redespacho_IdSalesOrder_Redespacho' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `SalesOrder_Redespacho_IdSalesOrder_Redespacho` `RedespachoSalesOrderId` INT NULL')
    
    # Fix spelling: Sincronization -> Synchronization (simplified)
    if 'SincronizationStatus_IdSincronizationStatus' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `SincronizationStatus_IdSincronizationStatus` `SynchronizationStatusId` INT NULL')
    
    # Drop unused column if exists
    if 'SalesOrder_IdSalesOrder' in existing_cols:
        op.drop_column('SalesOrder', 'SalesOrder_IdSalesOrder')


def downgrade() -> None:
    """
    Revert column names back to original (with typos).
    Note: This will NOT restore the dropped Descount column or SalesOrder_IdSalesOrder.
    """
    existing_cols = get_existing_columns()
    
    # MySQL/MariaDB syntax - revert to original names
    if 'Discount' in existing_cols and 'Descount' not in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `Discount` `Descount` DECIMAL(13,2) NULL')
    
    if 'BusinessPartnerId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `BusinessPartnerId` `BusinnesPartner_IdBusinnesPartner` INT NULL')
    
    if 'CompanyId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `CompanyId` `Company_IdCompany` INT NULL')
    
    if 'PaymentMethodId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `PaymentMethodId` `Company_PaymentMethod_IdCompany_PaymentMethod` INT NULL')
    
    if 'PaymentTermId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `PaymentTermId` `Company_PaymentTerm_IdCompany_PaymentTerm` INT NULL')
    
    if 'UtilizationId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `UtilizationId` `Company_Utilization_IdCompany_Utilization` INT NULL')
    
    if 'BranchId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `BranchId` `Company_Branch_IdCompany_Branch` INT NULL')
    
    if 'FreightId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `FreightId` `Company_Freight_IdCompany_Freight` INT NULL')
    
    if 'RedespachoSalesOrderId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `RedespachoSalesOrderId` `SalesOrder_Redespacho_IdSalesOrder_Redespacho` INT NULL')
    
    if 'SynchronizationStatusId' in existing_cols:
        op.execute('ALTER TABLE `SalesOrder` CHANGE COLUMN `SynchronizationStatusId` `SincronizationStatus_IdSincronizationStatus` INT NULL')
