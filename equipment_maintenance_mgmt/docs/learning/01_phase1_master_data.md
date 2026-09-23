# Phase 1: Master Data (Equipment, Category, Location)

> Day 1 · ~3 h · Outcome: equipment register with validations, warranty tracking and chatter.

## 1. LEARN

### 1.1 Models and fields
A model is a Python class that inherits `models.Model`. Odoo creates a PostgreSQL table from `_name`: `equipment.maintenance.equipment` → `equipment_maintenance_equipment`.

| Field type | Used for |
|---|---|
| `Char`, `Text`, `Html` | name, serial number, notes |
| `Date` | purchase date, warranty expiry |
| `Many2one` | category, location, responsible employee (`hr.employee`), company |
| `One2many` | `request_ids` (inverse of `request.equipment_id`) |
| `Monetary` + `currency_field` | purchase cost, total maintenance cost |
| `Selection` | warranty status |
| `Boolean active` | archiving (records are hidden, not deleted) |

Useful attributes include `required`, `index`, `copy=False` (serial not duplicated), `tracking=True` (changes logged in the chatter), `ondelete='restrict'`, `check_company=True` and `translate=True`.

### 1.2 Three kinds of validation
1. **SQL constraint.** In Odoo 19 this is a class attribute:
   ```python
   _serial_no_company_uniq = models.Constraint(
       'UNIQUE(serial_no, company_id)',
       'The serial number must be unique per company.',
   )
   ```
   It is enforced by PostgreSQL, so it holds even for imports or concurrent users. *(Before Odoo 19 this was the `_sql_constraints` list.)*
2. **Python constraint** (`@api.constrains`), for rules that SQL cannot express easily:
   ```python
   @api.constrains('purchase_date', 'warranty_expiry_date')
   def _check_dates(self):
       ...raise ValidationError(self.env._("..."))
   ```
3. **Business guard** (`UserError`) inside action methods. See Phase 2.

### 1.3 Computed fields
- `@api.depends(...)` tells the ORM **when** to recompute.
- **Stored** (`store=True`): written in the database, so it can be searched, grouped and sorted. Example: `total_maintenance_cost`.
- **Non-stored**: computed on every read. Right for values that depend on *today*, such as `warranty_state` (a stored value would go stale overnight).
- A non-stored field can still be **searched** with `search='_search_warranty_state'`, which converts the search into a date domain:
  ```python
  def _search_warranty_state(self, operator, value):
      if operator != 'in':          # Odoo 19 normalises '=' to 'in'
          return NotImplemented     # the ORM builds 'not in' by negation
      ...
      return Domain.OR(state_domains[state] for state in value if state in state_domains)
  ```

### 1.4 Hierarchical model (location)
`_parent_store = True` plus a `parent_path` field gives fast `child_of` searches. `complete_name` is a **recursive** stored compute (`recursive=True`) that produces "Colombo Plant / Workshop A". `_has_cycle()` prevents loops.

### 1.5 Mixins
`_inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']` adds the chatter, tracking, activities and the image fields (`image_1920` … `image_128`) with no extra code.

## 2. DESIGN

| Requirement (PDF) | Field |
|---|---|
| Equipment Name | `name` |
| Serial Number | `serial_no` (unique per company) |
| Category | `category_id` → `equipment.maintenance.category` |
| Location | `location_id` → `equipment.maintenance.location` (hierarchical) |
| Purchase Date | `purchase_date` |
| Warranty Expiry Date | `warranty_expiry_date` + computed `warranty_state`, `warranty_days_left` |
| Responsible Employee | `employee_id` → `hr.employee` |

Extras that add value: model, manufacturer, purchase cost, image, notes, archiving, request counters and total maintenance cost.

Category and location are **separate models** rather than Char fields. This gives clean grouping in reports and a controlled list of values.

## 3. BUILD
| File | Content |
|---|---|
| `models/equipment_maintenance_category.py` | category, `equipment_count` via `_read_group` |
| `models/equipment_maintenance_location.py` | hierarchical location |
| `models/equipment_maintenance_equipment.py` | the equipment model |
| `models/res_company.py`, `res_config_settings.py` | warranty alert days, default labour rate |
| `views/equipment_maintenance_equipment_views.xml` | list (warranty decorations), form (smart buttons, ribbon, notebook, chatter), kanban, search |
| `data/equipment_maintenance_category_data.xml` | 4 default categories (`noupdate`) |

Key techniques:
- `_compute_display_name` shows "CNC Lathe Machine [CNC-2023-0001]", and `_rec_names_search = ['name', 'serial_no']` lets users find equipment by serial number.
- `_read_group(domain, groupby, aggregates)` counts requests for **all** records in one query (no N+1 problem).
- `copy_data()` appends "(copy)" to the name when duplicating.

## 4. VERIFY
Automated tests are in `tests/test_equipment.py`:
- duplicate serial raises `IntegrityError`
- purchase in the future or warranty before purchase raises `ValidationError`
- `warranty_state` is right for none, expired, expiring and valid, and the search filters return the right records
- request counters, category count, location name and recursion

Manual checks: create equipment, check the warranty badge, filter *Warranty Expiring Soon*, archive and unarchive.

## 5. REFLECT
| Pitfall | Lesson |
|---|---|
| Storing a value that depends on today's date | Use a non-stored compute plus a search method |
| Counting in a loop with `search_count` per record | Use `_read_group` once for the whole recordset |
| `_sql_constraints` copied from old tutorials | Odoo 19 uses `models.Constraint` attributes |
| Using `_()` from `odoo` | Odoo 19 favours `self.env._()` with named placeholders |

**Check yourself**
1. Why is `warranty_state` not stored, while `total_maintenance_cost` is?
2. What does `ondelete='restrict'` on `category_id` prevent?
3. Why use an SQL constraint for the serial number instead of `@api.constrains`?
