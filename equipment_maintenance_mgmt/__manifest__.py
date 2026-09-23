# __manifest__.py: module description read by Odoo (Apps list, install order,
# data files). The file contains a single Python dict.
{
    'name': 'Equipment Maintenance Management',
    # <Odoo series>.<major>.<minor>.<patch>
    'version': '19.0.1.0.0',
    # App category shown in the Apps menu (Parent/Child)
    'category': 'Services/Maintenance',
    'summary': 'Equipment register, maintenance requests, technician activities, '
               'spare parts consumption and maintenance cost analysis',
    'description': """
Equipment Maintenance Management
================================
Manage the complete maintenance life cycle of company equipment:

* Equipment master with warranty tracking and responsible employee
* Maintenance requests with automatic numbering and workflow
  (New > Assigned > In Progress > Completed / Cancelled)
* Technician activities with labour hours and cost
* Spare parts consumption with cost
* Automatic labour, spare part and total maintenance cost calculation
* Equipment maintenance history, cost analysis and pending maintenance reports
* Technician / Manager security groups with record rules
    """,
    'author': 'Harsha Madushan',
    'maintainer': 'Harsha Madushan',
    'license': 'LGPL-3',
    # Modules installed before this one; their models and XML IDs can be used here
    #   mail: chatter/activities, hr: employees, hr_hourly_cost: employee hourly cost,
    #   product: spare parts
    'depends': ['base', 'mail', 'hr', 'hr_hourly_cost', 'product'],
    # Data files loaded at install/upgrade, IN THIS ORDER (a file can only
    # reference XML IDs defined in files loaded before it)
    'data': [
        # security first: groups are referenced by access rights, views and menus
        'security/equipment_maintenance_mgmt_groups.xml',
        'security/ir.model.access.csv',
        'security/equipment_maintenance_equipment_security.xml',
        'security/equipment_maintenance_request_security.xml',
        # data
        'data/ir_sequence_data.xml',
        'data/equipment_maintenance_category_data.xml',
        'data/equipment_maintenance_tag_data.xml',
        'data/mail_activity_type_data.xml',
        'data/ir_cron_data.xml',
        # views
        'views/equipment_maintenance_category_views.xml',
        'views/equipment_maintenance_location_views.xml',
        'views/equipment_maintenance_tag_views.xml',
        'views/equipment_maintenance_equipment_views.xml',
        'views/equipment_maintenance_activity_views.xml',
        'views/equipment_maintenance_spare_part_views.xml',
        'views/equipment_maintenance_request_views.xml',
        'views/res_config_settings_views.xml',
        # reports
        'report/equipment_maintenance_cost_report_views.xml',
        'report/equipment_maintenance_reports.xml',
        'report/equipment_maintenance_request_templates.xml',
        'report/equipment_maintenance_request_pending_templates.xml',
        'report/equipment_maintenance_equipment_templates.xml',
        # menus last: they reference the actions defined above
        'views/equipment_maintenance_mgmt_menus.xml',
    ],
    # Loaded only in databases created with demo data
    'demo': [
        'demo/equipment_maintenance_demo.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    # application=True: shown as an App with its own icon on the home screen
    'application': True,
}
