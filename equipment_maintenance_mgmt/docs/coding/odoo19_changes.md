# Odoo 19 Differences Used in This Module (verified in the source)

Each item was checked against the local Odoo 19 source (`D:\Odoo Server\V19\server\odoo\...`) and/or the Odoo documentation (Context7: `/odoo/odoo` branch 19.0, `/websites/odoo_master`).

| # | Topic | Before (≤ 17/18) | **Odoo 19** | Proof in source | Used in |
|---|---|---|---|---|---|
| 1 | SQL constraints | `_sql_constraints = [(name, sql, msg)]` | `_name = models.Constraint('SQL', 'msg')`; also `models.Index` | `odoo/orm/table_objects.py` (`TableObject.__set_name__`) | equipment, category, activity, spare part |
| 2 | Group organisation | `category_id` on `res.groups` | `res.groups.privilege` + `privilege_id` | `odoo/addons/base/models/res_groups_privilege.py`, `res_groups.py:36` | `security/equipment_maintenance_mgmt_groups.xml` |
| 3 | Group members | `users` | `user_ids` | `res_groups.py:17` | groups XML |
| 4 | User groups | `groups_id` | `group_ids`, `all_group_ids` (incl. implied, searchable) | `res_users.py:257-259` | technician domain, demo users |
| 5 | Report / action groups | `groups_id` | `group_ids` | `ir_actions_report.py`, `ir_actions.py` | history PDF |
| 6 | Translations | `from odoo import _` / `_('... %s') % x` | `self.env._('... %(x)s', x=...)` | `odoo/orm/environments.py:315` | all messages |
| 7 | Domains | lists + `expression.OR` | `from odoo.fields import Domain`; `Domain.OR/AND`, `~domain` | `odoo/orm/domains.py`; `addons/project/models/project_tags.py` | `_search_warranty_state` |
| 8 | Search on non-stored fields | many operators to handle | operators normalised to `in` / `not in`; `return NotImplemented` → the ORM negates | `addons/project/models/project_task.py::_search_is_closed` | `_search_warranty_state`, `_search_is_overdue` |
| 9 | Selection kanban columns | custom `group_expand` method | `group_expand=True` on a Selection (default expander) | `odoo/orm/fields_selection.py:88-90, 212` | request `state` |
| 10 | Aggregation | `group_operator='sum'` | `aggregator='sum'` | `odoo/orm/fields.py:174, 303` | cost fields |
| 11 | SQL report model | `init()` + `CREATE VIEW` | `_table_query` property returning `SQL` | `odoo/orm/models.py:427`; `addons/account/report/account_invoice_report.py:76` | cost report |
| 12 | List views | `<tree>` | `<list>` | all standard views | all views |
| 13 | Dynamic attributes | `attrs="{...}"`, `states=` | `invisible="expr"`, `readonly=`, `required=`, `column_invisible=` | since 17, standard in 19 | all views |
| 14 | Chatter | `<div class="oe_chatter">…` | `<chatter/>` | `addons/maintenance/views/maintenance_views.xml` | equipment, request forms |
| 15 | Kanban templates | `kanban-box` | `<t t-name="card">` (+ `menu`), `highlight_color` | `maintenance_views.xml:157-186` | kanbans |
| 16 | Settings layout | div-based | `<app>` / `<block>` / `<setting>` | `addons/maintenance/views/res_config_settings_views.xml` | settings |
| 17 | Demo data flag | `--without-demo=False` | `--with-demo` (demo is off by default) | `odoo/tools/config.py:233` | install doc |
| 18 | UoM precision name | "Product Unit of Measure" | "Product Unit" | `addons/uom/data/uom_data.xml:5-6` | spare part quantity |
| 19 | Comodel read access | | "Since Odoo 19, one must have read access to the comodel to modify the relation" (many2many) | `addons/hr/models/hr_employee.py::_check_access` | design note for HR relations |
| 20 | HR public data | | internal users read `hr.employee` through the `hr.employee.public` fallback; private fields raise `AccessError` | `hr_employee.py` (`search_fetch`, `fetch`, `_check_private_fields`) | `sudo()` for `hourly_cost` |
| 21 | Hourly cost field | `timesheet_cost` in `hr_timesheet` (≤ 14) | `hr_hourly_cost` module, `groups="hr.group_hr_user"` | `addons/hr_hourly_cost/models/hr_employee.py` | manifest dependency |
| 22 | Test users | manual create | `new_test_user(env, login, groups='a,b')` | `odoo/tests/common.py:195` | `tests/common.py` |
