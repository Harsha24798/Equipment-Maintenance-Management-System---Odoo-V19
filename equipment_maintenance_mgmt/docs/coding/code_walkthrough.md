# Code Walkthrough (file by file)

Read the files in this order. It follows how Odoo loads the module and how the business data flows.

## 1. `__manifest__.py`
Declares the dependencies and the **load order** of data files: security → data → views → reports → menus. Reason: an XML file can only `ref` IDs that are already loaded (groups before ACLs, actions before menus).

## 2. `models/`

### `res_company.py`, `res_config_settings.py`
Company-level settings: `maintenance_labour_rate` (Monetary) and `maintenance_warranty_alert_days`. The settings model uses `related=..., readonly=False`, so saving writes to the company. A dedicated `maintenance_currency_id` avoids clashing with other modules' settings fields.

### `equipment_maintenance_category.py`
Simple master data. Highlights:
- `models.Constraint('UNIQUE(name, company_id)')`
- `_compute_equipment_count` uses **`_read_group`**: one SQL query for all categories
- `action_view_equipment` reuses the equipment action through `_for_xml_id` and adds a domain and default context

### `equipment_maintenance_location.py`
A hierarchy with `_parent_store`, `parent_path` and a **recursive** stored `complete_name`. `_check_parent_id` uses `_has_cycle()`.

### `equipment_maintenance_equipment.py`
| Section | What to explain |
|---|---|
| `_inherit` | mail.thread (chatter/tracking), mail.activity.mixin (to-dos), image.mixin (photo) |
| `_rec_names_search` | find equipment by serial number in any many2one |
| `_serial_no_company_uniq` | Odoo 19 SQL constraint |
| `_compute_display_name` | "Name [Serial]" |
| `_compute_request_count` | `_read_group` twice (all / open) |
| `_compute_total_maintenance_cost` | stored; completed requests only; also `last_maintenance_date` |
| `_compute_warranty_state` + `_search_warranty_state` | non-stored because it depends on *today*; the search method translates states into date domains with `Domain.OR` |
| `_check_dates` | `@api.constrains` business validation |
| `copy_data` | "(copy)" suffix |
| actions | smart buttons, new request, print history |
| `_cron_warranty_expiry_reminder` | idempotent daily reminder |

### `equipment_maintenance_request.py` (the heart)
1. **Module constants:** `REQUEST_STATES`, `REQUEST_TYPES`, `PRIORITIES` (reused by the report model) and `ALLOWED_TRANSITIONS` (the workflow as data).
2. **Default method:** `_default_technician_domain` (users in the Technician group via `all_group_ids`).
3. **Fields:**
   - `state` is readonly with `group_expand=True`
   - related **stored** `category_id` / `location_id` support reporting
   - `work_activity_ids` avoids the mail mixin clash
   - 4 stored cost fields with `aggregator='sum'`
4. **Computes:**
   - `_compute_duration`
   - `_compute_is_overdue` + `_search_is_overdue`
   - `_compute_costs`: one method, 4 fields, the cost formula comment
5. **Constraints:** `_check_scheduled_date`, `_check_equipment_id`.
6. **CRUD:**
   - `create`: sequence per company, auto-assign, to-do
   - `write`: implicit assignment, replanning the to-do on a technician change
   - `_unlink_except_processed`
7. **Actions:** assign, start, complete (needs an activity; closes the to-do), cancel (removes the to-do), reset, print.
8. **Business helpers:** `_get_open_states`, `_check_state_transition`, `_schedule_technician_todo`, `_cron_overdue_requests`.

### `equipment_maintenance_line_mixin.py`
An AbstractModel shared by the lines. `create`, `write` and `@api.ondelete` call `_check_request_editable` (lines are frozen on completed or cancelled requests). It also provides stored `equipment_id` and `company_id` (for grouping and multi-company rules).

### `equipment_maintenance_activity.py`
- `_default_technician_id`: the request technician (from context `default_request_id`), else the current user
- `labour_rate`: editable stored compute with `precompute`; reads `hourly_cost` via `sudo()` (HR-restricted field), falling back to the company rate
- `cost` = hours × rate; SQL checks (hours > 0, rate ≥ 0); Python check (≤ 24 h)

### `equipment_maintenance_spare_part.py`
`product_id` limited to goods; `name` and `unit_cost` are editable computes from the product; `total_cost` = qty × unit cost; SQL checks.

## 3. `report/`
- `equipment_maintenance_cost_report.py`: `_auto = False` + `_table_query` (SQL). One row per request with dimensions and measures.
- `equipment_maintenance_cost_report_views.xml`: pivot, graph, list and search, plus the *Equipment Maintenance History* window action.
- `equipment_maintenance_reports.xml`: the 3 `ir.actions.report` records (binding to the Print menu, file names, group restriction).
- `*_templates.xml`: QWeb: `web.html_container` → `web.external_layout` → tables with `t-field`.

## 4. `security/`
- groups file: privilege + 2 groups (manager implies technician; admin is a member)
- `ir.model.access.csv`: the ACL matrix
- `*_security.xml`: company rules (global), technician rules (own requests and their lines), manager rules (all)

## 5. `views/`
| File | Views |
|---|---|
| category / location | list, form, search, action |
| equipment | list (warranty decorations), form (header buttons, smart buttons, ribbon, avatar image, notebook, chatter), kanban (card template), search (warranty filters, group-bys) |
| request | list (overdue decoration, badges, sums), form (statusbar, conditional buttons and readonly, ribbons, editable line lists, costs), kanban (grouped by state, priority progress bar), calendar, search; actions: all / my / pending |
| activity / spare part | analysis lists grouped by technician / product |
| settings | `<app>/<block>/<setting>` |
| menus | root with `web_icon`; Maintenance, Equipment, Reporting (manager), Configuration (manager) |

## 6. `data/` and `demo/`
- sequence, categories and activity types (`noupdate`), 2 daily crons
- demo: users with passwords equal to their logins; employees with hourly costs; locations; spare parts; 6 equipment; 8 requests pushed through the **real workflow** with `<function>` calls

## 7. `tests/`
`common.py` holds the fixtures. The 5 test files are described in [testing/test_plan.md](../testing/test_plan.md).
