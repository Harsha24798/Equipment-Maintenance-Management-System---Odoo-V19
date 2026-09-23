# Coding Standards Applied

Reference: [Odoo 19 coding guidelines](https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html) and PEP8. Each rule below says how the module applies it.

## 1. Module structure and file naming

| Guideline | Applied |
|---|---|
| Directories `models/`, `views/`, `security/`, `data/`, `demo/`, `report/`, `static/`, `tests/` | ✔ |
| One Python file per main model, named after the model | `equipment_maintenance_request.py` → `equipment.maintenance.request` ✔ |
| Inherited standard models in their own file | `res_company.py`, `res_config_settings.py` ✔ |
| Views: `<model>_views.xml`; menus: `<module>_menus.xml` | `equipment_maintenance_request_views.xml`, `equipment_maintenance_mgmt_menus.xml` ✔ |
| Security: `ir.model.access.csv`, groups in `<module>_groups.xml`, rules in `<model>_security.xml` | `equipment_maintenance_mgmt_groups.xml`, `equipment_maintenance_equipment_security.xml`, `equipment_maintenance_request_security.xml` ✔ |
| Data: `<main_model>_data.xml`; demo: `*_demo.xml` | `equipment_maintenance_category_data.xml`, `ir_sequence_data.xml`, `ir_cron_data.xml`, `equipment_maintenance_demo.xml` ✔ |
| Reports: SQL model `<report>.py` + `<report>_views.xml`; actions in `*_reports.xml`; templates in `*_templates.xml` | `equipment_maintenance_cost_report.py/_views.xml`, `equipment_maintenance_reports.xml`, `*_templates.xml` ✔ |
| File names only `[a-z0-9_]` | ✔ |

## 2. XML

| Guideline | Applied |
|---|---|
| 4-space indentation, `<?xml version="1.0" encoding="utf-8"?>`, root `<odoo>` | ✔ |
| View ID `<model_name>_view_<view_type>` | `equipment_maintenance_request_view_form`, `..._view_kanban` ✔ |
| View `name` = XML ID with dots | `equipment.maintenance.request.view.form` ✔ |
| Action ID `<model_name>_action` (+ `_<detail>`) | `equipment_maintenance_request_action`, `..._action_my`, `..._action_pending`, `..._action_history`, `..._action_report` ✔ |
| Menu ID `<model_name>_menu` / `<module>_menu_root` | `equipment_maintenance_request_menu`, `equipment_maintenance_menu_root` ✔ |
| Group ID `<module_name>_group_<name>` | `equipment_maintenance_mgmt_group_technician`, `..._group_manager` ✔ |
| Rule ID `<model_name>_rule_<concerned_group>` | `equipment_maintenance_request_rule_technician`, `..._rule_manager`, `..._rule_company` ✔ |
| Inherited view keeps the original ID; name has `.inherit.<module>` | `res_config_settings_view_form` / `res.config.settings.view.form.inherit.equipment_maintenance_mgmt` ✔ |
| Actions declared before the menus that use them | menus file loaded last ✔ |

## 3. Python

| Guideline | Applied |
|---|---|
| PEP8 | ruff `E,W,F,B,N`: *All checks passed* ✔ |
| Odoo's own ruff configuration (`server/ruff.toml`) | *All checks passed* (`I001` isort is advisory in Odoo's config; `__init__` import order is kept for registry loading) ✔ |
| Imports: stdlib → third-party → `odoo` → local, one group per block | e.g. `datetime` / `psycopg2` / `odoo...` / `.common` ✔ |
| Class name = CamelCase of the model | `EquipmentMaintenanceRequest` ✔ |
| Recordset variables named after the model; singletons singular | `for request in self`, `requests_to_assign` ✔ |
| Method prefixes `_compute_`, `_search_`, `_default_`, `_check_`, `action_`, `_onchange_`, `_cron_` | ✔ (no onchange needed: editable computes are used) |
| **Model element order**: private attributes → default methods → fields → SQL constraints → compute/search (in field order) → constrains/onchange → CRUD → actions → business methods | ✔ (see `equipment_maintenance_request.py`) |
| `@api.model_create_multi` for `create` | ✔ |
| `@api.ondelete(at_uninstall=False)` instead of overriding `unlink` | ✔ |
| Never `cr.commit()` | ✔ |
| Do not catch exceptions blindly | ✔ (no try/except in business code) |
| Propagate context (`with_company`, `with_context`) | sequence `with_company`, cost `with_company` ✔ |
| Translations: every user-facing string wrapped, **named placeholders**, formatting done by the translation function | `self.env._("Request %(name)s cannot ...", name=...)` ✔ |
| Think extendable: small overridable helpers | `_get_open_states`, `_check_state_transition`, `_schedule_technician_todo`, `_default_technician_domain`, `_check_request_editable` ✔ |
| Comments on complex logic | cost formula, transition table, sudo reason, Odoo 19 search normalisation ✔ |
| Avoid N+1 queries | `_read_group` for counters ✔ |
| Use `filtered`, `mapped`, `sorted` | ✔ |

## 4. Security by design
- ACL for **every** model (including the report). Record rules for technicians, managers and multi-company.
- `sudo()` used exactly once, documented: reading `hr.employee.hourly_cost` to default the rate.
- Business guards in Python (not only `invisible` in views).

## 5. How to re-check

```bash
# lint (Odoo rules, isort advisory)
ruff check --config "D:\Odoo Server\V19\server\ruff.toml" --extend-ignore I001 equipment_maintenance_mgmt
# PEP8 set
ruff check --select E,W,F,B,N --line-length 120 --per-file-ignores "__init__.py:F401" --per-file-ignores "__manifest__.py:B018" equipment_maintenance_mgmt
# references / view fields / manifest (no server)
python equipment_maintenance_mgmt/docs/tools/static_check.py
```
