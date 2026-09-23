# Phase 6: Automation, Data, Icons & UX Polish

> Day 3 · ~2.5 h · Outcome: a module that works out of the box (sequence, categories, crons), shows well (demo data, icon) and guides the user (empty states, filters, settings).

## 1. LEARN

### 1.1 Data vs demo, and `noupdate`
| File type | Loaded | Example |
|---|---|---|
| `data` | always | sequence, default categories, activity types, crons |
| `demo` | only in demo databases | users, equipment, requests |

`<data noupdate="1">` means *create once, never overwrite on upgrade*. This preserves user edits, for example a renamed category or a changed sequence prefix. Groups, views, menus and actions are **not** noupdate, so upgrades deliver fixes to them.

### 1.2 Demo data that follows the business rules
Instead of forcing `state` values, the demo file calls the **real workflow methods**:
```xml
<record id="request_cnc_completed" model="equipment.maintenance.request"> ... </record>
<function model="equipment.maintenance.request" name="action_start" eval="[[ref('request_cnc_completed')]]"/>
<record id="activity_cnc_1" model="equipment.maintenance.activity"> ... </record>
<function model="equipment.maintenance.request" name="action_complete" eval="[[ref('request_cnc_completed')]]"/>
```
The demo therefore exercises and proves the logic: sequence, dates, costs and activities. Dates are relative (`DateTime.today() - relativedelta(months=2)`), so the demo always looks current (overdue, expiring warranty, and so on).

### 1.3 Scheduled actions (`ir.cron`)
```xml
<record id="ir_cron_warranty_expiry_reminder" model="ir.cron">
    <field name="model_id" ref="model_equipment_maintenance_equipment"/>
    <field name="state">code</field>
    <field name="code">model._cron_warranty_expiry_reminder()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
</record>
```
Cron methods must be **idempotent**. The warranty reminder is not created twice, because existing activities of that type are checked first.

### 1.4 Settings screen
`res.config.settings` is a transient model. Our fields are `related='company_id.xxx', readonly=False`, so saving the settings writes to the company. The Odoo 19 view layout is `<app>` → `<block>` → `<setting>`.

### 1.5 App icon and description
- `static/description/icon.png` (128×128) is used by `web_icon="equipment_maintenance_mgmt,static/description/icon.png"` on the root menu and by the Apps list.
- `static/description/index.html` and `banner.png` form the app store page.
- They were generated reproducibly by `docs/tools/make_icons.py` (Pillow, bundled with Odoo): a teal gradient with a white gear and an amber wrench, in flat Odoo style. An `icon.svg` source is also provided.

### 1.6 UX details
- Empty-state help (`<p class="o_view_nocontent_smiling_face">`) on every action.
- Default filters: *My Requests + Pending* for technicians, and grouped lines for the analysis lists.
- Colour decorations: overdue requests in red, expired warranty in red, expiring warranty in orange. Plus badges, ribbons and priority stars.
- `optional="show/hide"` columns, `multi_edit="1"` on the request list, `sample="1"` placeholder data on empty views.

## 2. DESIGN
| Automation | Why |
|---|---|
| Technician to-do on assignment | Technicians see their work in the Activities systray |
| Daily overdue reminder | Nothing is forgotten after the scheduled date |
| Daily warranty reminder | Claim repairs under warranty before it expires |

**Demo scenario:** 3 users (technicians Kasun and Nimal, manager Dilani), 4 locations, 5 spare parts, 6 equipment (warranty valid, expiring, expired) and 8 requests covering *every* state, including an overdue one.

## 3. BUILD
| File | Content |
|---|---|
| `data/ir_sequence_data.xml`, `equipment_maintenance_category_data.xml`, `mail_activity_type_data.xml`, `ir_cron_data.xml` | base data |
| `demo/equipment_maintenance_demo.xml` | demo scenario |
| `views/res_config_settings_views.xml` | settings |
| `static/description/*` | icon, banner, index.html |

## 4. VERIFY
- [ ] A new request gets `MR/<year>/0000x`.
- [ ] *Settings > Technical > Scheduled Actions* lists the 2 crons. *Run Manually* creates the warranty activity on the "Diesel Generator" (warranty in 20 days) and posts the overdue note on the "Hydraulic Press" request.
- [ ] The Settings screen changes the default labour rate, and new activities use it.
- [ ] The home screen shows the icon.
- Automated: `test_cron_overdue_posts_message`, `test_cron_warranty_expiry_reminder`.

## 5. REFLECT
| Pitfall | Lesson |
|---|---|
| Demo records created with a forced `state` | They bypass the logic; call the workflow methods with `<function>` |
| Absolute dates in demo | Demo ages; use `relativedelta` from today |
| Non-idempotent cron | Duplicated activities every day; check before creating |

**Check yourself**
1. What happens to a renamed default category when the module is upgraded?
2. Why is the cron user `base.user_root`?
