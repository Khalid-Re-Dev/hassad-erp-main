# Phase F2.4 – Modern Navigation & User Flow Redesign

Modernization of Hassad ERP navigation to reflect accounting workflow order, improve usability, and enhance user orientation with breadcrumbs and quick actions.

---

## 1. Executive Summary

This phase introduces a hierarchical, workflow-centered navigation system for Hassad ERP:
- Sidebar redesigned into collapsible groups ordered by accounting process
- Toolbar with quick actions for frequent tasks
- Breadcrumb navigation to show current context and allow quick backtracking
- Seamless integration with existing routing, permissions, and session management

Primary goals:
- Reduce user cognitive load and clicks to reach target modules
- Match accountant mental model: Company → Branch → Users → Products → Sales → Purchases → Accounting → Reports
- Provide clear orientation (Where am I? How did I get here? Where can I go?)

---

## 2. Design Principles

- Mirror the ERP setup and transaction lifecycle
- Progressive disclosure (collapsible groups)
- Bilingual (English/Arabic) friendly; visual structure stays readable in RTL
- Permission-aware: show only what the user can access
- Non-invasive: routing, services, and session management remain intact

---

## 3. Navigation Hierarchy (Accounting Workflow Order)

1) Setup & Configuration
- Company → Branches → Users → Roles → Settings

2) Products & Inventory
- Categories → Products → Stock Movements → Inventory Valuation

3) Sales Operations
- Customers → POS → Sales History

4) Purchase Operations
- Suppliers → Purchase Orders → Goods Receipt → Purchase Invoices

5) Accounting & Finance
- Chart of Accounts → Journal Entries → Trial Balance

6) Reports & Analytics
- Reports (Financial, Inventory, Sales, Purchases)

This order drives the sidebar grouping, breadcrumb paths, and quick-access priorities.

---

## 4. Files Added/Updated

Added:
- `navigation.json` – master navigation configuration (hierarchical)
- `ui/components/navigation_widget.py` – hierarchical sidebar widget
- `ui/components/breadcrumb_widget.py` – breadcrumb navigation widget
- `docs/PHASE_F2_4_USER_FLOW.md` – this document

Updated:
- `ui/main_window.py` – integrates the new sidebar, toolbar, and breadcrumb; preserves dynamic routing

No breaking changes to business logic, services, or session manager.

---

## 5. Navigation Configuration (navigation.json)

Purpose: single source of truth for groups, modules, ordering, and quick actions.

Key sections:
- `navigation_hierarchy.workflow_order`: developer reference
- `navigation_groups[]`: groups with ordered modules and metadata
- `quick_actions[]`: toolbar actions bound to module IDs
- `breadcrumb_config`: presentation hints (separator, home visibility)

Example (excerpt):
```json
{
  "navigation_groups": [
    {
      "id": "setup",
      "name": "Setup & Configuration",
      "name_ar": "الإعداد والتكوين",
      "order": 1,
      "modules": [
        {"id": "company", "name": "Company Profile", "permission": "company.view", "order": 1},
        {"id": "branches", "name": "Branches", "permission": "branches.view", "order": 2}
      ]
    },
    {
      "id": "products",
      "name": "Products & Inventory",
      "order": 2,
      "modules": [ {"id": "categories", "order": 1}, {"id": "products", "order": 2} ]
    }
  ],
  "quick_actions": [
    {"id": "new_sale", "target_module": "pos", "shortcut": "Ctrl+N"}
  ]
}
```

Notes:
- Each module carries `permission` for runtime filtering
- Arabic labels (`name_ar`) and `icon` are supported
- The file intentionally lives at project root for simplicity

---

## 6. Sidebar Component (ui/components/navigation_widget.py)

Responsibilities:
- Load `navigation.json`
- Render collapsible groups in the specified order
- Filter modules by permissions
- Raise a `module_selected` signal with: (module_id, group_name, group_name_ar, module_name, module_name_ar)

Behavior:
- Clicking a group header toggles visibility (persisting collapse state is a future enhancement)
- Clicking a module emits selection without side effects in the widget itself
- The widget is theme-friendly (QSS applies via parent application stylesheet)

Developer hooks:
- `select_module(module_id)` – programmatic highlight
- `set_bilingual(show_arabic: bool)` – rebuilds labels with bilingual formatting

---

## 7. Breadcrumb Component (ui/components/breadcrumb_widget.py)

Responsibilities:
- Display current navigation path: Home › Group › Module
- Bilingual labels and small icon support
- Emit `breadcrumb_clicked(str)` when a parent crumb is clicked

Behavior:
- Last item is bold and disabled (context indicator)
- Clicking Home returns to dashboard
- Styling uses neutral surface to maximize readability

Developer hooks:
- `set_path(group_name, group_name_ar, module_id, module_name, module_name_ar, module_icon)`
- `reset_to_home()`
- `set_bilingual(True/False)`

---

## 8. Main Window Integration (ui/main_window.py)

Changes:
- Old flat `QListWidget` sidebar replaced by `NavigationWidget`
- Added `BreadcrumbWidget` above content stack
- Added `QToolBar` with quick actions
- New method `_navigate_to_module_by_id(module_id: str)` routes without a `QListWidgetItem`

Key integration points (excerpt):
```python
# Create toolbar and content area
self._create_toolbar()
content_area = self._create_content_area()

# Sidebar
sidebar = self._create_modern_sidebar()

# Hook navigation selection
def _on_navigation_module_selected(self, module_id, group_name, group_name_ar, module_name, module_name_ar):
    self.breadcrumb.set_path(group_name, group_name_ar, module_id, module_name, module_name_ar)
    self._navigate_to_module_by_id(module_id)

# Breadcrumb back-navigation
def _on_breadcrumb_clicked(self, item_id: str):
    if item_id == "dashboard":
        self._show_dashboard()
    else:
        self._navigate_to_module_by_id(item_id)
```

Routing behavior:
- Preserves original dynamic import, instantiation caching, and permission checks
- `MODULE_REGISTRY` remains the source for module path/class/permission
- Dashboard maps to index 0 in `QStackedWidget`

---

## 9. Toolbar (Quick Actions)

Initial actions:
- New Sale (Ctrl+N) → `pos`
- Reports (Ctrl+R) → `reports`

Guidelines:
- Keep shortcuts ergonomic and consistent
- Permissions are enforced at navigation time
- Add more actions by reading `navigation.json.quick_actions` (future enhancement: auto-bind)

---

## 10. Permission & Session Considerations

- Visibility: modules without permission are hidden in the sidebar
- Access control: even if navigated programmatically, permissions are re-checked before load
- Session handling: unchanged. Logout flow and session manager usage remain intact

---

## 11. Accounting Workflow Alignment

The navigation order and grouping ensure a proper sequence:
- Setup before transactions ensures master data integrity
- Product configuration precedes POS and Purchases
- Accounting reports (Trial Balance) follow postings
- Reports are last, relying on upstream data

This mirrors real-world ERP adoption and daily usage flows, reducing training time and navigation errors.

---

## 12. Theming & RTL Notes

- Widgets use neutral selectors and avoid hard-coded colors where possible
- RTL is compatible: breadcrumb separators and group labels remain readable
- Theme engine from Phase F2.1 continues to apply globally

---

## 13. Testing Checklist

Functional tests:
- Sidebar groups render in correct order
- Modules visible per role/permissions
- Clicking modules loads correct window and caches instance
- Breadcrumb updates on navigation and supports back-navigation
- Toolbar actions navigate as expected

Edge cases:
- Unknown module_id → graceful error message
- Permission denied → warning dialog (unchanged)
- Rapid switching → no duplicate widget creation, stack counts remain stable

Manual steps:
1) Launch app and login with admin user
2) Verify group order: Setup → Products → Sales → Purchases → Accounting → Reports
3) Navigate to Company, Branches, Users in order; verify breadcrumb
4) Navigate to POS via sidebar and via Ctrl+N
5) Logout and login with limited user; verify hidden modules

---

## 14. Migration & Backward Compatibility

- No module IDs changed; all IDs align with `MODULE_REGISTRY`
- Old `QListWidget`-based methods removed in favor of direct ID routing
- No changes to service bindings or data access patterns

Rollback plan:
- Revert `ui/main_window.py` to previous commit
- Remove `ui/components/*_widget.py` and `navigation.json`

---

## 15. Future Enhancements

- Persist collapsed state per user/session
- Read and auto-bind toolbar actions from `navigation.json.quick_actions`
- Add search/filter input above navigation for large module sets
- Add badges (e.g., approvals pending) next to modules
- Telemetry: log navigation dwell time for UX insights

---

## 16. Appendix – Developer Reference

Signals:
- `NavigationWidget.module_selected(str, str, str, str, str)`
- `BreadcrumbWidget.breadcrumb_clicked(str)`

Core methods:
- `MainWindow._navigate_to_module_by_id(module_id: str)` → routes by module ID
- `MainWindow._load_module_widget(module_path: str, class_name: str, module_id: str)` → dynamic import/instantiate

Data flow:
- User action → NavigationWidget signal → MainWindow updates breadcrumb → routing → module displayed

---

## 17. Conclusion

This phase delivers a modern, workflow-aligned navigation experience that improves orientation, reduces navigation time, and reflects best practices in ERP UX. The implementation is modular, theme-compatible, and respects existing routing and permissions.
