# Phase 4: Security (Groups, Access Rights, Record Rules)

> Day 2 · ~2 h · Outcome: technicians see only their work, managers see everything, and companies are isolated.

## 1. LEARN: the 4 security layers of Odoo

| Layer | Question it answers | Our file |
|---|---|---|
| **Groups** | *Who* is the user? | `security/equipment_maintenance_mgmt_groups.xml` |
| **Access rights** (ACL, `ir.model.access`) | May this group read / write / create / delete this **model** at all? | `security/ir.model.access.csv` |
| **Record rules** (`ir.rule`) | *Which records* of the model? | `security/*_security.xml` |
| **UI restrictions** (`groups=` on menus, fields, buttons) | What is **shown**? (convenience, not security) | views / menus |

The ACL is checked first; with no ACL line the model is inaccessible. Record rules then filter rows:
- **Global rules** (no group) are **AND**-ed. Used for multi-company.
- **Group rules** are **OR**-ed between the groups of the user. The manager's `[(1,'=',1)]` rule therefore widens the technician's restriction.

### 1.1 Odoo 19 novelty: privileges
In Odoo 19, groups are gathered under a **`res.groups.privilege`**. The user form shows one selection per privilege ("Equipment Maintenance: Technician / Manager"). This was verified in `odoo/addons/base/models/res_groups_privilege.py` and in the standard `maintenance` module:
```xml
<record id="res_groups_privilege_equipment_maintenance" model="res.groups.privilege">
    <field name="name">Equipment Maintenance</field>
    <field name="category_id" ref="base.module_category_supply_chain"/>
</record>
<record id="equipment_maintenance_mgmt_group_manager" model="res.groups">
    <field name="privilege_id" ref="res_groups_privilege_equipment_maintenance"/>
    <field name="implied_ids" eval="[(4, ref('equipment_maintenance_mgmt_group_technician'))]"/>
    <field name="user_ids" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
</record>
```
Group members are `user_ids`, and users have `group_ids` / `all_group_ids` (previously `users` / `groups_id`).

### 1.2 Access CSV format
```
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_request_technician,...,model_equipment_maintenance_request,equipment_maintenance_mgmt_group_technician,1,1,1,0
```
`model_<model_with_underscores>` is the XML ID Odoo creates automatically for each model.

### 1.3 Record rule domain variables
`user` (current user record), `company_ids` (allowed companies), `company_id`, `time`.

## 2. DESIGN: security matrix

| Model | Technician (ACL) | Technician (rule) | Manager |
|---|---|---|---|
| Category / Location / Equipment | Read | all (company) | CRUD |
| Maintenance Request | Read, Write, Create | `technician_id = user OR create_uid = user` | CRUD, all |
| Activity / Spare part | CRUD | lines of *their* requests (`request_id.technician_id` / `request_id.create_uid`) | CRUD, all |
| Cost analysis report | none | n/a | Read |

| UI element | Visible to |
|---|---|
| App menu, Maintenance, Equipment | Technician+ |
| Reporting, Configuration menus | Manager |
| Settings menu | Settings admin (`base.group_system`) |
| Equipment cost column and stat button, Print History | Manager |

**Business rationale**
- Technicians need to *report* problems (create) and *work* on their jobs, but must not change the asset register or see other technicians' jobs and costs.
- Deleting is a manager decision, and only possible for new or cancelled requests (`@api.ondelete`).
- Multi-company rules keep each company's equipment and requests separate.

## 3. BUILD
| File | Content |
|---|---|
| `security/equipment_maintenance_mgmt_groups.xml` | privilege + Technician + Manager |
| `security/ir.model.access.csv` | 13 access lines |
| `security/equipment_maintenance_equipment_security.xml` | company rules: equipment, category, location |
| `security/equipment_maintenance_request_security.xml` | company, technician and manager rules: request, activity, spare part, report |

Rules are inside `<data noupdate="1">`, so an administrator's customisations survive module upgrades.

The `hr.employee` access subtlety was checked in `addons/hr/models/hr_employee.py`: internal users without HR rights read employees through the `hr.employee.public` fallback (name, avatar and so on). Private fields such as `hourly_cost` raise `AccessError`, so the activity reads the rate with `sudo()` (Phase 3).

## 4. VERIFY
`tests/test_security.py` uses `with_user(...)`:
- Technician A's search returns only their request; reading Technician B's request raises `AccessError`.
- A technician who reports a request can read it (`create_uid` rule).
- A technician completes their own job end to end, including activity creation and cost.
- A technician cannot delete requests, create or edit equipment, add lines to another technician's request, or read the cost report.
- A manager sees and can cancel and delete everything.
- The technician domain includes managers, because the group is implied.

Manual: log in as `kasun` / `kasun` (demo) and compare with `dilani` / `dilani` (manager).

## 5. REFLECT
| Pitfall | Lesson |
|---|---|
| Hiding a menu and calling it security | Menus only hide; ACLs and rules protect data (RPC ignores the UI) |
| Forgetting line rules | A technician could read other requests' lines through the lines' own menu |
| Group rules thought to be AND-ed | They are OR-ed; global rules are AND-ed |
| Copying `category_id` / `users` from Odoo ≤ 18 | Odoo 19 uses `privilege_id` / `user_ids` |

**Check yourself**
1. A technician creates a request and assigns it to a colleague. Can they still see it? Why?
2. Why is the cost-report ACL only for managers?
3. Why are record rules declared with `noupdate="1"`?
