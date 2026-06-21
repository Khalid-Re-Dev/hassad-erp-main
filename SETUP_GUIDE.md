# Hassad ERP System - Complete Setup Guide

This guide will walk you through setting up and running the Hassad ERP system from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Database Setup](#database-setup)
4. [Running the Application](#running-the-application)
5. [Default Login Credentials](#default-login-credentials)
6. [Testing the System](#testing-the-system)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

1. **Python 3.11 or higher**
   - Download from: https://www.python.org/downloads/
   - Verify installation: `python --version`

2. **PostgreSQL 14 or higher**
   - Download from: https://www.postgresql.org/download/
   - Verify installation: `psql --version`

3. **Git** (optional, for version control)
   - Download from: https://git-scm.com/downloads/

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 500MB for application + database storage
- **Display**: 1024x768 minimum resolution (1920x1080 recommended)

## Installation

### Step 1: Extract or Clone the Project

If you have a ZIP file:
\`\`\`bash
# Extract the ZIP file to your desired location
# Navigate to the extracted folder
cd hassad-erp
\`\`\`

If using Git:
\`\`\`bash
git clone <repository-url>
cd hassad-erp
\`\`\`

### Step 2: Create Virtual Environment

**On Windows:**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# You should see (venv) in your terminal prompt
