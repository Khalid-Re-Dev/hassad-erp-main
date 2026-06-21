# Phase F2.4 - Testing & Validation Guide

This document provides comprehensive testing procedures for the modernized navigation system.

---

## Test Environment Setup

### Prerequisites
1. PostgreSQL database running with Hassad ERP schema
2. Virtual environment activated
3. All dependencies installed (`pip install -r requirements.txt`)
4. Test data seeded (users with different roles)

### Launch Application
```powershell
cd E:\Trying\hassad-erp-main
.\venv\Scripts\activate
python main.py
```

---

## Test Suite 1: Navigation Structure

### Test 1.1: Hierarchical Groups Display
**Objective**: Verify navigation groups appear in correct accounting workflow order

**Steps**:
1. Login as admin user
2. Observe left sidebar

**Expected Results**:
- Groups appear in order:
  1. ⚙️ Setup & Configuration
  2. 📦 Products & Inventory
  3. 🛒 Sales Operations
  4. 🚚 Purchase Operations
  5. 💼 Accounting & Finance
  6. 📊 Reports & Analytics

**Pass Criteria**: Groups display in exact order with correct icons ✅

---

### Test 1.2: Collapsible Groups
**Objective**: Verify group collapse/expand functionality

**Steps**:
1. Click "Setup & Configuration" header
2. Observe module list
3. Click header again
4. Repeat for other groups

**Expected Results**:
- First click: modules hide, arrow changes from ▼ to ▶
- Second click: modules show, arrow changes from ▶ to ▼
- Other groups remain unaffected

**Pass Criteria**: All groups collapse/expand independently ✅

---

### Test 1.3: Module Visibility
**Objective**: Verify modules appear in correct order within groups

**Steps**:
1. Expand "Setup & Configuration" group

**Expected Results**:
Modules appear in order:
1. 🏢 Company Profile
2. 🏪 Branches
3. 👥 Users
4. 🔐 Roles & Permissions
5. ⚙️ System Settings

**Pass Criteria**: All modules display with icons in correct order ✅

---

## Test Suite 2: Navigation Functionality

### Test 2.1: Module Navigation
**Objective**: Verify clicking modules loads correct windows

**Steps**:
1. Click "Company Profile"
2. Verify company window loads
3. Click "Users"
4. Verify users window loads
5. Repeat for 5 different modules

**Expected Results**:
- Correct window displays for each module
- Content stack index changes
- No errors in console

**Pass Criteria**: All modules load successfully ✅

---

### Test 2.2: Module Instance Caching
**Objective**: Verify modules are cached and reused

**Steps**:
1. Click "Products"
2. Note window loads (DEBUG: "Successfully loaded module: products")
3. Click "Categories"
4. Click "Products" again
5. Check logs for "Reusing cached module: products"

**Expected Results**:
- First load: widget created
- Second load: cached widget reused
- No duplicate instantiation

**Pass Criteria**: Caching works, no memory leaks ✅

---

### Test 2.3: Module Highlight
**Objective**: Verify selected module is highlighted

**Steps**:
1. Click "Company Profile"
2. Observe button styling

**Expected Results**:
- Selected module: blue background (#3498db), white text, bold
- Other modules: transparent background, light text

**Pass Criteria**: Visual distinction is clear ✅

---

## Test Suite 3: Breadcrumb Navigation

### Test 3.1: Breadcrumb Display
**Objective**: Verify breadcrumb updates correctly

**Steps**:
1. Click "Company Profile" in Setup group
2. Observe breadcrumb bar (top of content area)

**Expected Results**:
```
🏠 Home › Setup & Configuration › 🏢 Company Profile
```
- "Home" is clickable (blue)
- "Setup & Configuration" is clickable (blue)
- "Company Profile" is bold and disabled (gray)

**Pass Criteria**: Breadcrumb displays correct path ✅

---

### Test 3.2: Breadcrumb Navigation
**Objective**: Verify breadcrumb links work

**Steps**:
1. Navigate to Company Profile (breadcrumb: Home › Setup › Company)
2. Click "Home" in breadcrumb
3. Verify dashboard loads
4. Navigate to Products
5. Click "Products & Inventory" group in breadcrumb

**Expected Results**:
- Clicking "Home": returns to dashboard, breadcrumb resets to "🏠 Home"
- Clicking group: no action (groups are not directly navigable in current implementation)

**Pass Criteria**: Home navigation works ✅

---

### Test 3.3: Breadcrumb Icon Display
**Objective**: Verify module icons appear in breadcrumb

**Steps**:
1. Navigate to various modules with icons
2. Check breadcrumb

**Expected Results**:
- Icons appear before module names in breadcrumb
- Icons match sidebar icons

**Pass Criteria**: Icons display correctly ✅

---

## Test Suite 4: Toolbar & Quick Actions

### Test 4.1: Toolbar Visibility
**Objective**: Verify toolbar displays at top

**Steps**:
1. Observe top of window below menu bar

**Expected Results**:
- Toolbar visible with actions:
  - "🛒 New Sale"
  - Separator
  - "📊 Reports"

**Pass Criteria**: Toolbar displays correctly ✅

---

### Test 4.2: Quick Action Navigation
**Objective**: Verify toolbar buttons navigate correctly

**Steps**:
1. Click "🛒 New Sale"
2. Verify POS window loads
3. Click "📊 Reports"
4. Verify Reports window loads

**Expected Results**:
- Buttons navigate to correct modules
- Breadcrumb updates accordingly

**Pass Criteria**: All quick actions work ✅

---

### Test 4.3: Keyboard Shortcuts
**Objective**: Verify shortcuts trigger navigation

**Steps**:
1. Press `Ctrl+N`
2. Verify POS window loads
3. Press `Ctrl+R`
4. Verify Reports window loads

**Expected Results**:
- Shortcuts work globally from any module
- Navigation is instant

**Pass Criteria**: Shortcuts function correctly ✅

---

## Test Suite 5: Permission-Based Visibility

### Test 5.1: Admin User Access
**Objective**: Verify admin sees all modules

**Steps**:
1. Login as admin user
2. Count visible groups and modules

**Expected Results**:
- All 6 groups visible
- All ~20 modules visible

**Pass Criteria**: Admin has full access ✅

---

### Test 5.2: Limited User Access
**Objective**: Verify limited users see only authorized modules

**Steps**:
1. Create user with only "sales.view" permission
2. Logout and login as that user
3. Observe navigation

**Expected Results**:
- Only "Sales Operations" group visible (or modules user has permission for)
- Hidden modules: Company, Users, Accounting, etc.
- No error messages

**Pass Criteria**: Permission filtering works ✅

---

### Test 5.3: Permission Check on Navigation
**Objective**: Verify permission checks at navigation time

**Steps**:
1. Login as limited user
2. Try to navigate to unauthorized module via breadcrumb/direct URL

**Expected Results**:
- Access denied message dialog
- User remains on current page

**Pass Criteria**: Unauthorized access blocked ✅

---

## Test Suite 6: Session & Logout

### Test 6.1: Logout Functionality
**Objective**: Verify logout works correctly

**Steps**:
1. Click "🚪 Logout | تسجيل الخروج" button at bottom of sidebar
2. Confirm logout in dialog

**Expected Results**:
- Confirmation dialog appears
- After confirmation: returns to login screen
- Session cleared

**Pass Criteria**: Logout completes successfully ✅

---

### Test 6.2: Session Persistence
**Objective**: Verify user session persists during navigation

**Steps**:
1. Login as user
2. Navigate to 5+ different modules
3. Check user info at top of sidebar

**Expected Results**:
- User name remains visible
- Role remains visible
- No session loss

**Pass Criteria**: Session persists ✅

---

## Test Suite 7: Theme Compatibility

### Test 7.1: Light Theme
**Objective**: Verify navigation works in light theme

**Steps**:
1. Menu bar → View → Theme → Light Theme
2. Observe navigation styling

**Expected Results**:
- Breadcrumb: light background (#ecf0f1)
- Groups: colored headers (per group color)
- Modules: dark sidebar (#2c3e50) with light text

**Pass Criteria**: Theme applies correctly ✅

---

### Test 7.2: Dark Theme
**Objective**: Verify navigation works in dark theme

**Steps**:
1. Menu bar → View → Theme → Dark Theme
2. Observe navigation styling

**Expected Results**:
- Overall darker color scheme
- Navigation remains readable
- Contrast maintained

**Pass Criteria**: Dark theme compatible ✅

---

### Test 7.3: RTL Layout
**Objective**: Verify RTL compatibility

**Steps**:
1. Menu bar → View → Layout → Enable RTL
2. Observe navigation and breadcrumb

**Expected Results**:
- Sidebar remains on left (position unchanged)
- Text alignment adjusts where applicable
- Breadcrumb separator remains "›"

**Pass Criteria**: RTL doesn't break navigation ✅

---

## Test Suite 8: Edge Cases & Error Handling

### Test 8.1: Rapid Navigation
**Objective**: Verify rapid clicking doesn't break navigation

**Steps**:
1. Rapidly click 10 different modules
2. Check for errors or duplicate widgets

**Expected Results**:
- All navigations complete
- No widget duplication
- Stack count remains stable

**Pass Criteria**: No crashes or errors ✅

---

### Test 8.2: Unknown Module ID
**Objective**: Verify error handling for invalid module

**Steps**:
1. (Developer test) Manually call `_navigate_to_module_by_id("invalid_module")`
2. Observe behavior

**Expected Results**:
- Error dialog: "Module 'invalid_module' not found in registry"
- User remains on current page

**Pass Criteria**: Graceful error handling ✅

---

### Test 8.3: Empty Navigation Config
**Objective**: Verify behavior if navigation.json is missing

**Steps**:
1. Rename navigation.json temporarily
2. Launch application
3. Check console for warnings

**Expected Results**:
- Warning in console: "navigation.json not found"
- Sidebar shows no groups (empty)
- No crash

**Pass Criteria**: Degrades gracefully ✅

---

## Test Suite 9: Accounting Workflow Order Validation

### Test 9.1: Setup First
**Objective**: Verify Setup & Configuration is group #1

**Steps**:
1. Observe group order

**Expected Results**:
- Setup & Configuration is first group (order: 1)

**Pass Criteria**: ✅

---

### Test 9.2: Products Before Sales
**Objective**: Verify inventory comes before sales

**Steps**:
1. Observe group order

**Expected Results**:
- Products & Inventory (order: 2) appears before Sales Operations (order: 3)

**Pass Criteria**: ✅

---

### Test 9.3: Sales and Purchases Before Accounting
**Objective**: Verify transactions precede accounting

**Steps**:
1. Observe group order

**Expected Results**:
- Sales Operations (order: 3) and Purchase Operations (order: 4) appear before Accounting & Finance (order: 5)

**Pass Criteria**: ✅

---

### Test 9.4: Reports Last
**Objective**: Verify reports come after all data entry

**Steps**:
1. Observe group order

**Expected Results**:
- Reports & Analytics (order: 6) is last group

**Pass Criteria**: ✅

---

## Test Suite 10: Performance

### Test 10.1: Initial Load Time
**Objective**: Measure sidebar rendering time

**Steps**:
1. Note timestamp when main window appears
2. Note timestamp when sidebar completes rendering

**Expected Results**:
- Sidebar renders in < 1 second

**Pass Criteria**: Fast initial load ✅

---

### Test 10.2: Navigation Response Time
**Objective**: Measure navigation speed

**Steps**:
1. Click module
2. Measure time until window displays

**Expected Results**:
- First load: < 2 seconds
- Cached load: < 0.5 seconds

**Pass Criteria**: Responsive navigation ✅

---

## Summary Checklist

| Test Suite | Test Count | Status |
|------------|-----------|--------|
| Navigation Structure | 3 | ⬜ |
| Navigation Functionality | 3 | ⬜ |
| Breadcrumb Navigation | 3 | ⬜ |
| Toolbar & Quick Actions | 3 | ⬜ |
| Permission-Based Visibility | 3 | ⬜ |
| Session & Logout | 2 | ⬜ |
| Theme Compatibility | 3 | ⬜ |
| Edge Cases | 3 | ⬜ |
| Workflow Order | 4 | ⬜ |
| Performance | 2 | ⬜ |
| **TOTAL** | **29** | ⬜ |

---

## Known Issues & Limitations

1. **Group breadcrumb navigation**: Clicking group names in breadcrumb currently has no action (future enhancement)
2. **Collapsed state persistence**: Group collapse state doesn't persist across sessions (future enhancement)
3. **Toolbar auto-binding**: Quick actions are hard-coded; auto-reading from navigation.json planned

---

## Regression Testing

After any changes to navigation code, re-run:
- Test Suite 2 (Navigation Functionality)
- Test Suite 3 (Breadcrumb Navigation)
- Test Suite 5 (Permission-Based Visibility)

---

## Automated Testing (Future)

Consider implementing:
- Pytest fixtures for navigation testing
- Mock permission manager for unit tests
- UI automation with PyQt test framework

---

## Sign-off

**Tested by**: _________________  
**Date**: _________________  
**Result**: ☐ PASS ☐ FAIL  
**Notes**: _________________
