# Equipment Maintenance Management System (Odoo 19)

![Equipment Maintenance Management](equipment_maintenance_mgmt/static/description/banner.png)

Odoo 19 practical evaluation by **Harsha Madushan**.

| Path | Content |
|---|---|
| [`equipment_maintenance_mgmt/`](equipment_maintenance_mgmt/) | The Odoo 19 addon (installable module) |
| [`equipment_maintenance_mgmt/README.md`](equipment_maintenance_mgmt/README.md) | Functional documentation: purpose, installation, usage |
| [`equipment_maintenance_mgmt/TECHNICAL.md`](equipment_maintenance_mgmt/TECHNICAL.md) | Technical documentation: models, fields, workflow, design decisions |
| [`equipment_maintenance_mgmt/docs/`](equipment_maintenance_mgmt/docs/README.md) | Learning pack, evaluation criteria coverage, test plan, presentation |
| [`Odoo_19_Practical_Evaluation_Harsha_Updated.pdf`](Odoo_19_Practical_Evaluation_Harsha_Updated.pdf) | The evaluation brief |

## Quick start

Clone the repository and add **the clone folder** to the Odoo addons path, so Odoo finds the `equipment_maintenance_mgmt` module inside it:

```
git clone https://github.com/Harsha24798/Equipment-Maintenance-Management-System---Odoo-V19.git
odoo-bin -c odoo.conf --addons-path="<odoo>/addons,<path>/Equipment-Maintenance-Management-System---Odoo-V19" -d <db> -i equipment_maintenance_mgmt
```

Run the tests:

```
odoo-bin -c odoo.conf -d <test_db> -i equipment_maintenance_mgmt --test-enable --test-tags /equipment_maintenance_mgmt --stop-after-init
```
