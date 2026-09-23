# Phase 5: Reporting

> Day 2–3 · ~3.5 h · Outcome: the three required reports (history, cost analysis, pending) plus a printable work order.

## 1. LEARN

### 1.1 Two kinds of reports in Odoo
| Kind | Technique | Our reports |
|---|---|---|
| **Analytical** (interactive) | window action with pivot, graph and list views, optionally on a **SQL-view model** | Maintenance Cost Analysis, Pending Maintenance, Equipment Maintenance History |
| **Printable** (PDF) | `ir.actions.report` + **QWeb** template rendered by wkhtmltopdf | Work Order, Equipment History, Pending Summary |

### 1.2 SQL-view report model (Odoo 19 style)
A model with `_auto = False` has no table created by the ORM. Its rows come from a query. Odoo 19 lets you declare the query as the `_table_query` property, returning an `odoo.tools.SQL` object:
```python
class EquipmentMaintenanceCostReport(models.Model):
    _name = 'equipment.maintenance.cost.report'
    _auto = False

    @property
    def _table_query(self):
        return SQL("""
            SELECT r.id AS id, r.id AS request_id, r.equipment_id, e.category_id, ...,
                   COALESCE(r.labour_cost, 0) AS labour_cost, ...
            FROM equipment_maintenance_request r
            JOIN equipment_maintenance_equipment e ON e.id = r.equipment_id
            JOIN res_company c ON c.id = r.company_id
        """)
```
This mirrors the pattern in `addons/hr_timesheet/report/timesheets_analysis_report.py`. Every field is `readonly=True`. The measures declare `aggregator='sum'`. It only works because the request costs are **stored** (Phase 3).

**Why a SQL view and not the request model directly?** It is an optimised, flat, read-only dataset for analysis. It has its own access rules (managers only) and can be extended with more joins without touching the transactional model.

### 1.3 Pivot and graph views
```xml
<pivot>
    <field name="category_id" type="row"/>
    <field name="request_date" interval="month" type="col"/>
    <field name="total_cost" type="measure"/>
</pivot>
<graph type="bar" stacked="1"> ... </graph>
```

### 1.4 QWeb PDF reports
- `ir.actions.report` has `report_type=qweb-pdf` and `report_name` (the template XML ID). `binding_model_id` adds it to the **Print** menu. `print_report_name` sets the file name. `group_ids` restricts it to groups.
- Template structure: `web.html_container` → loop over `docs` → `web.external_layout` (company header/footer) → `<div class="page">`.
- `t-field` renders a field with its widget (monetary, date, selection label). `t-out` renders an expression. `t-options="{'widget': 'monetary', 'display_currency': o.currency_id}"` formats computed sums.

Following the guidelines, report **actions** live in `report/equipment_maintenance_reports.xml` and **templates** in `report/*_templates.xml`.

## 2. DESIGN
| PDF requirement | Delivered |
|---|---|
| Equipment maintenance history | Menu *Reporting > Equipment Maintenance History* (completed requests grouped by equipment); the history tab on the equipment form; **PDF "Equipment Maintenance History"** with every request, its activities and parts, and cost totals |
| Maintenance cost analysis | SQL-view model with pivot (category × month), stacked bar graph and list, plus filters and group-bys (equipment, category, location, technician, type, month) |
| Pending maintenance report | Menu *Reporting > Pending Maintenance* (open states, grouped by technician, overdue in red); **PDF "Pending Maintenance Summary"** (select requests > Print) |
| (extra) Work order | **PDF** on each request, with signature lines |

## 3. BUILD
| File | Content |
|---|---|
| `report/equipment_maintenance_cost_report.py` | SQL-view model |
| `report/equipment_maintenance_cost_report_views.xml` | pivot, graph, list, search, cost action, history action |
| `report/equipment_maintenance_reports.xml` | 3 `ir.actions.report` |
| `report/equipment_maintenance_request_templates.xml` | work order |
| `report/equipment_maintenance_equipment_templates.xml` | equipment history |
| `report/equipment_maintenance_request_pending_templates.xml` | pending summary |
| request views | `equipment_maintenance_request_action_pending` |

## 4. VERIFY
`tests/test_reports.py` checks:
- the SQL view row equals the request costs (3 000 + 400 = 3 400)
- `_read_group` on the view groups by category
- all 3 QWeb templates render (`_render_qweb_html`), and the pending report excludes completed requests

Manual: open pivot and graph, switch measures, and print each PDF. PDF printing needs wkhtmltopdf, which is bundled with the Windows installer (`thirdparty`).

## 5. REFLECT
| Pitfall | Lesson |
|---|---|
| Non-stored cost fields | A SQL view cannot read them; store the computes |
| Old `init()` + `CREATE VIEW` pattern | Still valid, but `_table_query` is simpler (no view to drop or recreate) |
| Forgetting ACLs for the report model | "Access error" when opening the menu; give read access to managers |
| Putting business logic in QWeb | Keep templates for presentation; compute in Python |

**Check yourself**
1. Why does the cost report have a single row per request?
2. How would you add "cost per location per quarter"? (Hint: no code, just group-by and interval.)
3. Where is the manager-only restriction of the history PDF declared?
