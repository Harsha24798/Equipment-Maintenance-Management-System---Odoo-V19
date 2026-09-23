# Phase 3: Activities, Spare Parts & Cost Engine

> Day 2 · ~3 h · Outcome: labour, spare part and total maintenance cost computed automatically and reliably.

## 1. LEARN

### 1.1 One2many line models
A request owns lines: `work_activity_ids = One2many('equipment.maintenance.activity', 'request_id')`. The line holds `request_id = Many2one(..., ondelete='cascade')`, so deleting the request deletes its lines. In the form, `<list editable="bottom">` gives inline editing.

### 1.2 Sharing code with an `AbstractModel` mixin
Activities and spare parts share fields and rules. Instead of copying them, we use:
```python
class EquipmentMaintenanceLineMixin(models.AbstractModel):
    _name = 'equipment.maintenance.line.mixin'
    # request_id, equipment_id, company_id, currency_id + locking rules
```
Each line model then declares `_inherit = ['equipment.maintenance.line.mixin']`. An AbstractModel has **no table**; its fields are copied into each inheriting model.

> In `models/__init__.py` the mixin is imported **before** the models that inherit it, so it is in the registry when they are built. This is why `__init__` imports stay one per line in a deliberate order.

### 1.3 Dependency chains
```
activity.cost = hours_spent × labour_rate                  @api.depends('hours_spent', 'labour_rate')
part.total_cost = quantity × unit_cost                     @api.depends('quantity', 'unit_cost')
request.labour_cost = Σ work_activity_ids.cost             @api.depends('work_activity_ids.cost', ...)
request.spare_part_cost = Σ spare_part_ids.total_cost
request.total_cost = labour_cost + spare_part_cost
equipment.total_maintenance_cost = Σ completed requests    @api.depends('request_ids.state', 'request_ids.total_cost', ...)
```
Dotted dependencies (`work_activity_ids.cost`) make the ORM recompute the parent when a child changes, is added or is removed. All levels are **stored**, so list views can sum them, pivot views can aggregate them and the SQL report can read them.

One compute method can fill **several fields** (`_compute_costs` sets 4 fields). This is efficient because the lines are read once.

### 1.4 Editable computed defaults: `compute` + `store` + `readonly=False` + `precompute`
The labour rate and unit cost must **default** from master data but stay **editable**:
```python
labour_rate = fields.Monetary(compute='_compute_labour_rate', store=True,
                              readonly=False, precompute=True)
```
- It is recomputed when its dependency (technician or product) changes. This is the modern replacement for `@api.onchange`, and it also works through the ORM and imports, not only in the UI.
- A manual value is kept until a dependency changes again.
- `precompute=True` computes the value before the INSERT, which saves an UPDATE.

### 1.5 Monetary fields
`fields.Monetary(currency_field='currency_id')`. The currency is related to the company, so amounts display with the right symbol and rounding. `aggregator='sum'` (Odoo 19 name, formerly `group_operator`) controls grouped totals.

### 1.6 Reading protected data safely with `sudo()`
`hr.employee.hourly_cost` has `groups="hr.group_hr_user"`, so a technician may not read it. We read it as superuser **only to compute the default**:
```python
employee = activity.technician_id.sudo().with_company(company).employee_id
activity.labour_rate = employee.hourly_cost or company.maintenance_labour_rate
```

## 2. DESIGN
| PDF requirement | Field |
|---|---|
| Activity Description | `activity.name` |
| Technician | `activity.technician_id` (default: the request technician) |
| Hours Spent | `activity.hours_spent` (> 0, ≤ 24) |
| Labour Rate | `activity.labour_rate` (employee hourly cost, else company default) |
| Cost | `activity.cost` |
| Product | `spare_part.product_id` (goods only: `type = 'consu'`) |
| Quantity | `spare_part.quantity` (> 0) |
| Unit Cost | `spare_part.unit_cost` (product cost, editable) |
| Total Cost | `spare_part.total_cost` |
| Labour / Spare Part / Total Maintenance Cost | `request.labour_cost`, `spare_part_cost`, `total_cost` |

**Integrity rule:** once a request is completed or cancelled, its lines are frozen. `create`, `write` and `@api.ondelete` in the mixin raise a `UserError`, and the view also makes the tabs readonly.

## 3. BUILD
| File | Content |
|---|---|
| `models/equipment_maintenance_line_mixin.py` | shared fields + locking |
| `models/equipment_maintenance_activity.py` | activity, labour rate, cost, constraints |
| `models/equipment_maintenance_spare_part.py` | spare part, unit cost, total, constraints |
| cost fields in `models/equipment_maintenance_request.py` | `_compute_costs` |
| `views/equipment_maintenance_activity_views.xml`, `..._spare_part_views.xml` | analysis lists (grouped) |

### Worked example (demo request on the CNC lathe)
| Line | Calculation | Amount |
|---|---|---|
| Nimal: replace spindle bearings | 4 h × 2 000 | 8 000 |
| Kasun: lubrication and alignment | 2 h × 1 500 | 3 000 |
| **Labour cost** | | **11 000** |
| Ball Bearing 6205 | 4 × 850 | 3 400 |
| **Spare part cost** | | **3 400** |
| **Total maintenance cost** | | **14 400** |

## 4. VERIFY
`tests/test_costs.py` checks:
- the rate from the employee (1 500), the company fallback (1 000) and a manual override (800)
- the spare part default from the product cost and its override
- the multi-line totals (4 600)
- recompute after editing or deleting lines
- that the equipment total counts completed requests only
- the SQL and Python constraints

## 5. REFLECT
| Pitfall | Lesson |
|---|---|
| `@api.onchange` for defaults | Only runs in the UI form; use editable stored computes |
| Non-stored totals | Cannot be summed in lists or grouped in pivots |
| Duplicating fields in two line models | Use an AbstractModel mixin |
| Reading HR-restricted fields as the user | `AccessError` for technicians; use `sudo()` for that single value |

**Check yourself**
1. What happens to `request.total_cost` when a spare part line is deleted? Why?
2. Why is `labour_rate` stored *and* editable?
3. Why do we restrict products to `type = 'consu'`?
