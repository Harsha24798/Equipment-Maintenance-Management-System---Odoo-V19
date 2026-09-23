from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user


class EquipmentMaintenanceCommon(TransactionCase):
    """Shared fixtures: two technicians, one manager, master data and helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.maintenance_labour_rate = 1000.0
        cls.company.maintenance_warranty_alert_days = 30
        cls.today = fields.Date.context_today(cls.env['equipment.maintenance.equipment'])

        cls.technician_a = new_test_user(
            cls.env, login='tech_a', name='Technician A',
            groups='equipment_maintenance_mgmt.equipment_maintenance_mgmt_group_technician')
        cls.technician_b = new_test_user(
            cls.env, login='tech_b', name='Technician B',
            groups='equipment_maintenance_mgmt.equipment_maintenance_mgmt_group_technician')
        cls.manager = new_test_user(
            cls.env, login='maint_manager', name='Maintenance Manager',
            groups='equipment_maintenance_mgmt.equipment_maintenance_mgmt_group_manager')

        # Technician A has an employee with an hourly cost, B has none (-> company rate)
        cls.employee_a = cls.env['hr.employee'].create({
            'name': 'Technician A',
            'user_id': cls.technician_a.id,
            'hourly_cost': 1500.0,
        })

        cls.category = cls.env['equipment.maintenance.category'].create({'name': 'Test Machinery'})
        cls.location = cls.env['equipment.maintenance.location'].create({'name': 'Test Workshop'})
        cls.equipment = cls.env['equipment.maintenance.equipment'].create({
            'name': 'Test Lathe',
            'serial_no': 'TEST-SN-001',
            'category_id': cls.category.id,
            'location_id': cls.location.id,
            'employee_id': cls.employee_a.id,
            'purchase_date': cls.today - timedelta(days=365),
            'warranty_expiry_date': cls.today + timedelta(days=365),
        })
        cls.product_bearing = cls.env['product.product'].create({
            'name': 'Test Bearing',
            'type': 'consu',
            'standard_price': 200.0,
        })
        cls.product_oil = cls.env['product.product'].create({
            'name': 'Test Oil',
            'type': 'consu',
            'standard_price': 50.0,
        })

    @classmethod
    def _create_request(cls, **values):
        vals = {'equipment_id': cls.equipment.id, 'request_type': 'corrective'}
        vals.update(values)
        return cls.env['equipment.maintenance.request'].create(vals)

    @classmethod
    def _add_activity(cls, request, hours=2.0, technician=None, **values):
        vals = {
            'request_id': request.id,
            'name': 'Test activity',
            'technician_id': (technician or cls.technician_a).id,
            'hours_spent': hours,
        }
        vals.update(values)
        return cls.env['equipment.maintenance.activity'].create(vals)

    @classmethod
    def _add_spare_part(cls, request, product=None, quantity=1.0, **values):
        vals = {
            'request_id': request.id,
            'product_id': (product or cls.product_bearing).id,
            'quantity': quantity,
        }
        vals.update(values)
        return cls.env['equipment.maintenance.spare.part'].create(vals)

    def _run_to_in_progress(self, request, technician=None):
        request.technician_id = technician or self.technician_a
        request.action_start()
        return request
