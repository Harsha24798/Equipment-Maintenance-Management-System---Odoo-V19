# Evaluation Criteria Coverage

Each criterion below is mapped to where it is implemented and how it is proven. Paths are relative to the module root.

Legend: ✅ covered · 🧪 covered by automated test

---

## 1. Requirement Understanding & Functional Analysis (15%)

| Check | Status | Evidence |
|---|---|---|
| Understanding of the business flow | ✅ | `docs/business/business_flow.md` (actors, end-to-end flowchart, status table, cost model, reports → decisions) |
| Required models and relationships | ✅ | 7 business models + 1 abstract mixin + 1 report model; ER diagram in `TECHNICAL.md §2` |
| Logical workflow | ✅ 🧪 | New → Assigned → In Progress → Completed / Cancelled (+ Reset); `ALLOWED_TRANSITIONS` in `models/equipment_maintenance_request.py`; `tests/test_request_workflow.py` |
| Business validations | ✅ 🧪 | 16 rules, listed in `TECHNICAL.md §3.3` |
| Missing details → reasonable assumptions | ✅ | `TECHNICAL.md §3.6 Assumptions` (technician = user, labour rate source, no stock moves, equipment cost = completed jobs, who may process, deletion policy...) |
| Requirement → implementation mapping | ✅ | `docs/business/business_flow.md §7` |

## 2. Odoo Framework Knowledge (20%)

### Models & ORM
| Check | Status | Evidence |
|---|---|---|
| Proper model creation, `_name`, `_description` | ✅ | every model: `equipment.maintenance.category / location / equipment / request / tag / activity / spare.part / cost.report / line.mixin` |
| Correct inheritance usage | ✅ | mixins `_inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']`; own **AbstractModel** `equipment.maintenance.line.mixin` inherited by activity and spare part; extension of `res.company` and `res.config.settings`; **view inheritance** `views/res_config_settings_views.xml` |
| Many2one | ✅ | `equipment_id`, `category_id`, `location_id`, `employee_id`, `technician_id`, `product_id`, `request_id`, `parent_id` |
| One2many | ✅ | `equipment.request_ids`, `request.work_activity_ids`, `request.spare_part_ids`, `location.child_ids`, `category.equipment_ids` |
| Many2many | ✅ 🧪 | `request.tag_ids` ↔ `tag.request_ids` (explicit relation table `equipment_maintenance_request_tag_rel`); `test_tags_many2many` |

### ORM methods
| Method | Status | Evidence |
|---|---|---|
| `create()` | ✅ 🧪 | `EquipmentMaintenanceRequest.create` (`@api.model_create_multi`: sequence, auto-assign, to-do); `EquipmentMaintenanceLineMixin.create` (lock check) |
| `write()` | ✅ 🧪 | `EquipmentMaintenanceRequest.write` (technician → Assigned, to-do replanning); `EquipmentMaintenanceLineMixin.write` (lock check) |
| `unlink()` | ✅ 🧪 | deletion rules via `@api.ondelete(at_uninstall=False)` (`_unlink_except_processed`, `_unlink_except_locked_request`), the Odoo-recommended hook for `unlink()`; `test_unlink_rules`, `test_lines_locked_after_completion` |
| `search()` | ✅ | `_cron_warranty_expiry_reminder`, `_cron_overdue_requests`, `_onchange_equipment_id`; `_read_group` for counters |
| `browse()` | ✅ | `EquipmentMaintenanceLineMixin.create/write` (`browse(request_ids)`), `EquipmentMaintenanceActivity._default_technician_id` |

### Odoo features
| Feature | Status | Evidence |
|---|---|---|
| Sequences | ✅ 🧪 | `data/ir_sequence_data.xml` (`MR/%(year)s/00001`), taken in `create()` `with_company`; `test_sequence_number` |
| Chatter tracking | ✅ | `mail.thread` + `tracking=True` on equipment and request fields; `<chatter/>` in forms |
| Computed fields | ✅ 🧪 | stored (`total_cost`, `total_maintenance_cost`, `duration`), non-stored + `search=` (`warranty_state`, `is_overdue`), editable (`labour_rate`, `unit_cost`), recursive (`complete_name`), multi-field (`_compute_costs`) |
| Onchange methods | ✅ 🧪 | `_onchange_equipment_id` returns a warning for duplicate open requests and warranty; `test_onchange_equipment_warnings`. Editable defaults use computes (the modern replacement for onchange) |
| Constraints | ✅ 🧪 | SQL: `models.Constraint` (serial unique, tag unique, category unique, hours > 0, qty > 0, costs ≥ 0). Python: `_check_dates`, `_check_parent_id`, `_check_scheduled_date`, `_check_equipment_id`, `_check_technician_id`, `_check_hours_spent` |
| Default values | ✅ | `default=fields.Date.context_today`, company, priority, state, hours; methods `_default_technician_id`, `_default_color`, `_default_technician_domain` |

## 3. Python Development Quality (15%)

| Check | Status | Evidence |
|---|---|---|
| Code structure | ✅ | one file per model; class element order per Odoo guidelines (attributes → defaults → fields → constraints → computes → constrains/onchange → CRUD → actions → business) |
| PEP8 compliance | ✅ | `ruff --select E,W,F,B,N`: *All checks passed*; Odoo `server/ruff.toml`: *All checks passed* |
| Meaningful names | ✅ | `_check_state_transition`, `_schedule_technician_todo`, `_check_request_editable`, `requests_to_assign`, `LOCKED_REQUEST_STATES` |
| Readability | ✅ | constants for selections and transitions, small helpers, no deep nesting |
| Comments on complex logic | ✅ | cost formula, transition table, `sudo()` reason, Odoo 19 search normalisation, completed-only equipment cost |
| No duplication | ✅ | line **mixin**; shared selection constants reused by the report model; `_get_open_states()` reused by computes, reports and the onchange |
| Exception handling | ✅ | `UserError` for business refusals, `ValidationError` for data rules, `AccessError` from the framework; no bare try/except; translated messages with named placeholders (`self.env._`) |

## 4. Module Structure & Development Standards (10%)

| Check | Status | Evidence |
|---|---|---|
| Addon structure and folders | ✅ | `models/ views/ security/ data/ demo/ report/ static/ tests/ docs/` + `README.md`, `TECHNICAL.md` |
| Proper manifest | ✅ | `__manifest__.py`: name, version `19.0.1.0.0`, category, summary, description, author, license, depends, ordered data, demo, images, application |
| Module naming | ✅ | `equipment_maintenance_mgmt` (does not clash with the standard `maintenance`) |
| Separate Python file per model | ✅ | `models/equipment_maintenance_{category,location,equipment,request,tag,line_mixin,activity,spare_part}.py`, `res_company.py`, `res_config_settings.py` |
| File naming per Odoo guidelines | ✅ | `docs/coding/coding_standards.md §1` |

## 5. XML Views & UI (15%)

| Check | Status | Evidence |
|---|---|---|
| Form views | ✅ | equipment, request, category, location |
| List views with `<list>` | ✅ | all models (decorations, badges, `optional`, `sum`, `multi_edit`, editable lists) |
| Search views | ✅ | all models (filters, date filters, group-bys, `filter_domain`) |
| Kanban views | ✅ | equipment (image card), request (grouped by state, priority progress bar, activities, avatar) |
| Other views | ✅ | calendar, activity, pivot, graph |
| Buttons | ✅ | header workflow buttons with `invisible` expressions, confirm dialog, print |
| Statusbar | ✅ | `<field name="state" widget="statusbar" statusbar_visible="..."/>` |
| Notebook pages | ✅ | request: Activities / Spare Parts / Resolution / Cancellation; equipment: History / Notes |
| Smart buttons | ✅ | equipment: Open/All Requests, Maintenance Cost; category: Equipment |
| Field positioning | ✅ | `oe_title`, grouped sections (Equipment / Request / Timing / Costs), ribbons, avatar image |
| Naming standards | ✅ | `<model>_view_<type>`, `<model>_action[_detail]`, `<model>_menu`, `equipment_maintenance_menu_root` |

## 6. Security (10%)

| Check | Status | Evidence |
|---|---|---|
| User group / Manager group | ✅ | `security/equipment_maintenance_mgmt_groups.xml`: Technician (user) and Manager (implies Technician), Odoo 19 `res.groups.privilege` |
| `ir.model.access.csv` with CRUD permissions | ✅ | `security/ir.model.access.csv` (15 lines, every model, including the report) |
| User-based restriction ("user sees own requests") | ✅ 🧪 | `equipment_maintenance_request_rule_technician`: `technician_id = user OR create_uid = user`; line rules through `request_id`; `test_technician_sees_only_own_requests`, `test_technician_cannot_read_other_request` |
| Manager full access | ✅ 🧪 | `*_rule_manager` `[(1, '=', 1)]`; `test_manager_sees_everything` |
| Multi-company | ✅ | global `*_rule_company` on every model |

## 7. Business Logic & Validation (10%)

| Example in criteria | Status | Implementation |
|---|---|---|
| Workflow transitions / button actions | ✅ 🧪 | `action_assign/start/complete/cancel/reset_to_new` + `_check_state_transition` |
| Prevent invalid state changes | ✅ 🧪 | `test_invalid_transitions`, `test_cannot_cancel_completed` |
| Prevent duplicate records | ✅ 🧪 | unique serial (SQL), unique tag and category names; onchange warning for duplicate open requests on the same equipment |
| Prevent users approving their own requests (analogue) | ✅ 🧪 | `_check_is_assigned_technician`: a user cannot start or complete work that is not assigned to them (e.g. a request they reported); only the assigned technician or a manager; `test_only_assigned_technician_processes_request` |
| Mandatory field validations | ✅ 🧪 | `required=` fields; `_check_technician_id` (technician mandatory once assigned); completion needs an activity |
| Data consistency | ✅ 🧪 | lines locked on closed requests; delete only new or cancelled; scheduled ≥ request date; no requests on archived equipment |

## 8. Documentation & Delivery (5%)

| Check | Status | Evidence |
|---|---|---|
| README: purpose, installation, functional overview | ✅ | `README.md` §1–4 |
| TECHNICAL: models, fields, workflow, design decisions | ✅ | `TECHNICAL.md` §2 (models and fields), §3.1 (workflow), §3.6 (assumptions), §3.7 (design decisions) |
| Tests and evidence | ✅ | 59 automated tests; `docs/testing/test_plan.md`; `docs/evidence/` |
| GitHub repository, feature-wise commits | ✅ | local git history with one commit per feature (see `git log`), ready to push to your GitHub repository |
