# Database Schema Documentation

## Overview

The Hassad ERP System uses PostgreSQL with SQLAlchemy ORM. All tables use UUID primary keys for distributed sync compatibility and include standard timestamp fields.

## Core Design Principles

1. **UUID Primary Keys**: All tables use UUID for primary keys to support future offline sync
2. **UTC Timestamps**: All datetime fields use UTC timezone
3. **Soft Deletes**: Records are marked as deleted rather than physically removed
4. **Version Control**: Hash-based conflict detection for sync
5. **Audit Trail**: Comprehensive change tracking via audit_logs table

## Tables

### companies

Stores company/legal entity information for multi-company support.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Company legal name |
| trade_name | VARCHAR(255) | | Trading name |
| tax_id | VARCHAR(50) | UNIQUE | Tax ID number |
| registration_number | VARCHAR(50) | UNIQUE | Business registration |
| email | VARCHAR(255) | | Primary email |
| phone | VARCHAR(50) | | Primary phone |
| address | TEXT | | Physical address |
| city | VARCHAR(100) | | City |
| state | VARCHAR(100) | | State/Province |
| country | VARCHAR(100) | NOT NULL | Country code |
| postal_code | VARCHAR(20) | | Postal/ZIP code |
| currency | VARCHAR(3) | NOT NULL | Currency (ISO 4217) |
| fiscal_year_start | VARCHAR(2) | NOT NULL | Fiscal year start month |
| is_active | BOOLEAN | NOT NULL | Active status |
| logo_url | VARCHAR(500) | | Company logo URL |
| website | VARCHAR(255) | | Company website |
| notes | TEXT | | Additional notes |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |
| version_hash | VARCHAR(64) | | Conflict detection hash |

### branches

Stores branch/location information within companies.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| company_id | UUID | FK, NOT NULL | Parent company |
| name | VARCHAR(255) | NOT NULL | Branch name |
| code | VARCHAR(50) | NOT NULL, UNIQUE | Unique branch code |
| email | VARCHAR(255) | | Branch email |
| phone | VARCHAR(50) | | Branch phone |
| address | TEXT | | Physical address |
| city | VARCHAR(100) | | City |
| state | VARCHAR(100) | | State/Province |
| country | VARCHAR(100) | NOT NULL | Country code |
| postal_code | VARCHAR(20) | | Postal/ZIP code |
| is_active | BOOLEAN | NOT NULL | Active status |
| is_main | BOOLEAN | NOT NULL | Main/HQ branch flag |
| manager_name | VARCHAR(255) | | Branch manager |
| notes | TEXT | | Additional notes |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |
| version_hash | VARCHAR(64) | | Conflict detection hash |

### users

Stores user accounts with authentication information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| company_id | UUID | FK, NOT NULL | Company |
| branch_id | UUID | FK | Default branch |
| username | VARCHAR(100) | NOT NULL, UNIQUE | Login username |
| email | VARCHAR(255) | NOT NULL, UNIQUE | Email address |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt password hash |
| first_name | VARCHAR(100) | NOT NULL | First name |
| last_name | VARCHAR(100) | NOT NULL | Last name |
| phone | VARCHAR(50) | | Phone number |
| is_active | BOOLEAN | NOT NULL | Active status |
| is_superuser | BOOLEAN | NOT NULL | Superuser flag |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |
| version_hash | VARCHAR(64) | | Conflict detection hash |

### roles

Stores role definitions for RBAC.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Role name |
| code | VARCHAR(50) | NOT NULL, UNIQUE | Role code |
| description | TEXT | | Role description |
| is_active | BOOLEAN | NOT NULL | Active status |
| is_system | BOOLEAN | NOT NULL | System role flag |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |
| version_hash | VARCHAR(64) | | Conflict detection hash |

### permissions

Stores permission definitions for granular access control.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Permission name |
| code | VARCHAR(100) | NOT NULL, UNIQUE | Permission code |
| module | VARCHAR(50) | NOT NULL | Module name |
| description | TEXT | | Permission description |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |
| version_hash | VARCHAR(64) | | Conflict detection hash |

### user_roles

Many-to-many association between users and roles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | PK, FK | User ID |
| role_id | UUID | PK, FK | Role ID |

### role_permissions

Many-to-many association between roles and permissions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| role_id | UUID | PK, FK | Role ID |
| permission_id | UUID | PK, FK | Permission ID |

### audit_logs

Immutable audit trail of all system changes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| user_id | UUID | FK | User who performed action |
| action | VARCHAR(50) | NOT NULL | Action type |
| entity_type | VARCHAR(100) | NOT NULL | Entity type (table) |
| entity_id | UUID | | Affected entity ID |
| old_values | JSON | | Previous values |
| new_values | JSON | | New values |
| ip_address | VARCHAR(45) | | User IP address |
| user_agent | TEXT | | User agent string |
| notes | TEXT | | Additional notes |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |
| version_hash | VARCHAR(64) | | Conflict detection hash |

### settings

Flexible key-value configuration storage.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| company_id | UUID | FK | Company (NULL for system) |
| category | VARCHAR(50) | NOT NULL | Setting category |
| key | VARCHAR(100) | NOT NULL | Setting key |
| value | TEXT | | Setting value |
| data_type | VARCHAR(20) | NOT NULL | Data type hint |
| description | TEXT | | Setting description |
| is_system | VARCHAR(10) | NOT NULL | System setting flag |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | | Soft delete timestamp |
| version_hash | VARCHAR(64) | | Conflict detection hash |

## Relationships

### One-to-Many

- Company → Branches
- Company → Settings
- Branch → Users
- User → AuditLogs

### Many-to-Many

- Users ↔ Roles (via user_roles)
- Roles ↔ Permissions (via role_permissions)

## Indexes

All foreign keys are automatically indexed. Additional indexes:

- users.username
- users.email
- roles.code
- permissions.code
- audit_logs.action
- audit_logs.entity_type
- settings.category
- settings.key

## Future Extensions (Phase 2+)

The schema is designed to accommodate future modules:

- **Accounting**: Chart of accounts, journal entries, ledgers
- **Inventory**: Products, stock movements, warehouses
- **Sales**: Invoices, receipts, customers
- **Purchases**: Purchase orders, suppliers, bills
- **Reporting**: Custom reports, dashboards

Each future module will follow the same design principles established in Phase 1.
