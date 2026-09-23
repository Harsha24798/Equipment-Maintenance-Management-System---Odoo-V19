# Phase 2: Maintenance Request & Workflow

> Day 1–2 · ~4 h · Outcome: numbered requests moving through a guarded state machine, with technician to-dos.

## 1. LEARN

### 1.1 Automatic numbering with `ir.sequence`
`data/ir_sequence_data.xml` declares code `equipment.maintenance.request` with prefix `MR/%(year)s/` and padding 5, giving `MR/2026/00001`.

The number is taken in `create()` (not as a field default). This way no number is consumed when the user opens a form and discards it:
```python
@api.model_create_multi
def create(self, vals_list):
    default_name = self.env._('New')
    for vals in vals_list:
        if vals.get('name', default_name) == default_name:
            company_id = vals.get('company_id') or self.env.company.id
            vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code(
                'equipment.maintenance.request') or default_name
    ...
    return super().create(vals_list)
```
`@api.model_create_multi` receives a **list** of dicts, so batch creation stays fast.

### 1.2 State machine
- `state` is a `Selection`, `readonly=True` (changed only by buttons), tracked, and `group_expand=True` so the kanban always shows every column.
- The allowed transitions are **data**, declared once:
  ```python
  ALLOWED_TRANSITIONS = {
      'assigned': ('new',),
      'in_progress': ('assigned',),
      'completed': ('in_progress',),
      'cancelled': ('new', 'assigned', 'in_progress'),
      'new': ('cancelled',),
  }
  ```
- Each button method calls `_check_state_transition(target)`, which raises a `UserError` with a clear message. This protects the rule even if the method is called through RPC, not only from the UI.

| Button | Method | Extra rule |
|---|---|---|
| Assign | `action_assign` | technician required; plans a to-do |
| Start | `action_start` | sets `date_start` |
| Complete | `action_complete` | ≥ 1 activity; sets `date_done`; marks the to-do done |
| Cancel | `action_cancel` | removes the to-do (confirmation dialog in the view) |
| Reset to New | `action_reset_to_new` | clears the technician and dates |

### 1.3 Overriding `write()` for implicit transitions
Choosing a technician on a *New* request should assign it without an extra click:
```python
if vals.get('technician_id') and 'state' not in vals:
    requests_to_assign = self.filtered(lambda r: r.state == 'new')
res = super().write(vals)
if requests_to_assign:
    requests_to_assign.write({'state': 'assigned'})
```
Always call `super()` and return its result.

### 1.4 Delete protection
```python
@api.ondelete(at_uninstall=False)
def _unlink_except_processed(self): ...
```
This is the Odoo ≥ 15 pattern, preferred over overriding `unlink()`. `at_uninstall=False` means the check is skipped when the module is uninstalled.

### 1.5 Activities (to-dos)
`mail.activity.mixin` provides:
- `activity_schedule(xmlid, user_id=..., date_deadline=..., summary=...)`
- `activity_feedback([xmlid])` to mark it done
- `activity_unlink([xmlid])` to remove it

We define our own activity type `mail_activity_data_maintenance_todo` in `data/mail_activity_type_data.xml`.

### 1.6 Odoo 19 view syntax
- **Header buttons:** `invisible="state != 'new'"`. In Odoo ≥ 17 this is a Python expression; `attrs` and `states` no longer exist.
- **Statusbar:** `<field name="state" widget="statusbar" statusbar_visible="new,assigned,in_progress,completed"/>`
- **Conditional readonly:** `readonly="state in ('completed', 'cancelled')"`
- **Ribbons:** `<widget name="web_ribbon" title="Completed" bg_color="text-bg-success" invisible="state != 'completed'"/>`
- **Chatter:** `<chatter/>`

## 2. DESIGN
| PDF requirement | Implementation |
|---|---|
| Request Number (automatic sequence) | `name` + `ir.sequence` |
| Equipment | `equipment_id` (required, not archived) |
| Request Date | `request_date` (default today) |
| Request Type | `request_type` selection |
| Description | `description` Html |
| Assigned Technician | `technician_id` → `res.users` limited to the Technician group |
| Priority | `priority` '0'..'3' with stars |
| Status + workflow | `state` + action methods |

**Why is the technician a `res.users` and not an `hr.employee`?** Record rules compare with `user.id`, activities are assigned to users, and a technician must log in to work on the request. The hourly cost is still read from the user's linked employee (Phase 3).

Extras: scheduled date, overdue flag (computed + searchable), start/done dates and duration, resolution notes, cancellation reason.

## 3. BUILD
| File | Content |
|---|---|
| `models/equipment_maintenance_request.py` | model, workflow, overrides, cron |
| `data/ir_sequence_data.xml` | sequence (`noupdate`) |
| `data/mail_activity_type_data.xml` | to-do and warranty activity types |
| `views/equipment_maintenance_request_views.xml` | form, list, kanban (grouped by state), calendar, search, 3 actions |

The technician domain is built by a method, because it depends on a group's database ID:
```python
technician_id = fields.Many2one('res.users', domain=lambda self: self._default_technician_domain())
# -> [('share', '=', False), ('all_group_ids', 'in', <technician group id>)]
```
`all_group_ids` (Odoo 19) includes **implied** groups, so managers are proposed too.

## 4. VERIFY
`tests/test_request_workflow.py` covers:
- sequence format and uniqueness
- creation through a `Form` (like the UI)
- auto-assign on create and on write, plus the to-do planned for the right user
- a full happy path, every invalid transition, and completion without an activity
- cancel/reset, deleting a running request refused, lines locked after completion
- the scheduled date constraint, archived equipment, overdue compute and search, duration, the overdue cron

## 5. REFLECT
| Pitfall | Lesson |
|---|---|
| Taking the sequence in `default=` | Numbers get burnt for discarded forms; take it in `create()` |
| Checking the state only with `invisible` in the view | The UI is not security; also guard in Python |
| Naming the lines One2many `activity_ids` | It clashes with `mail.activity.mixin.activity_ids`; renamed `work_activity_ids` |
| Overriding `unlink()` to block deletes | Use `@api.ondelete(at_uninstall=False)` |

**Check yourself**
1. Why is `state` readonly in the model?
2. What would break if `create()` used `@api.model` with a single dict?
3. How does the kanban show an empty "Completed" column?
