from datetime import timedelta

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import EquipmentMaintenanceCommon


@tagged('post_install', '-at_install')
class TestEquipment(EquipmentMaintenanceCommon):

    def test_display_name_includes_serial(self):
        self.assertEqual(self.equipment.display_name, 'Test Lathe [TEST-SN-001]')

    def test_name_search_by_serial_number(self):
        found = self.env['equipment.maintenance.equipment'].name_search('TEST-SN-001')
        self.assertIn(self.equipment.id, [rec_id for rec_id, _name in found])

    def test_serial_number_unique_per_company(self):
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self.env['equipment.maintenance.equipment'].create({
                'name': 'Duplicate',
                'serial_no': 'TEST-SN-001',
                'category_id': self.category.id,
            })
            self.env.flush_all()

    def test_purchase_date_not_in_future(self):
        with self.assertRaises(ValidationError):
            self.equipment.purchase_date = self.today + timedelta(days=1)

    def test_warranty_after_purchase(self):
        with self.assertRaises(ValidationError):
            self.equipment.warranty_expiry_date = self.equipment.purchase_date - timedelta(days=1)

    def test_warranty_state_compute(self):
        cases = [
            (False, 'none'),
            (self.today - timedelta(days=1), 'expired'),
            (self.today + timedelta(days=10), 'expiring'),
            (self.today + timedelta(days=31), 'valid'),
        ]
        for expiry, expected in cases:
            with self.subTest(expiry=expiry):
                self.equipment.warranty_expiry_date = expiry
                self.assertEqual(self.equipment.warranty_state, expected)

    def test_warranty_state_search(self):
        equipment_model = self.env['equipment.maintenance.equipment']
        self.equipment.warranty_expiry_date = self.today + timedelta(days=5)
        self.assertIn(self.equipment, equipment_model.search([('warranty_state', '=', 'expiring')]))
        self.assertNotIn(self.equipment, equipment_model.search([('warranty_state', '=', 'expired')]))
        self.assertNotIn(self.equipment, equipment_model.search([('warranty_state', '!=', 'expiring')]))

    def test_request_counters(self):
        self._create_request()
        cancelled = self._create_request()
        cancelled.action_cancel()
        self.assertEqual(self.equipment.request_count, 2)
        self.assertEqual(self.equipment.open_request_count, 1)

    def test_copy_keeps_serial_unique(self):
        # serial_no is copy=False and required: copying must ask for a new serial
        copy = self.equipment.copy({'serial_no': 'TEST-SN-002'})
        self.assertEqual(copy.name, 'Test Lathe (copy)')

    def test_category_equipment_count(self):
        self.assertEqual(self.category.equipment_count, 1)

    def test_cron_warranty_expiry_reminder(self):
        activity_type = self.env.ref('equipment_maintenance_mgmt.mail_activity_data_warranty_expiry')
        self.equipment.warranty_expiry_date = self.today + timedelta(days=10)
        equipment_model = self.env['equipment.maintenance.equipment']
        equipment_model._cron_warranty_expiry_reminder()
        reminders = self.equipment.activity_ids.filtered(lambda a: a.activity_type_id == activity_type)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders.user_id, self.technician_a)
        # idempotent: a second run does not duplicate the reminder
        equipment_model._cron_warranty_expiry_reminder()
        reminders = self.equipment.activity_ids.filtered(lambda a: a.activity_type_id == activity_type)
        self.assertEqual(len(reminders), 1)

    def test_location_complete_name_and_recursion(self):
        child = self.env['equipment.maintenance.location'].create({
            'name': 'Bay 1', 'parent_id': self.location.id})
        self.assertEqual(child.complete_name, 'Test Workshop / Bay 1')
        with self.assertRaises(ValidationError):
            self.location.parent_id = child
