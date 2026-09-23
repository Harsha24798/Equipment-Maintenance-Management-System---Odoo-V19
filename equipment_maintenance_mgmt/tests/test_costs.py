from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import EquipmentMaintenanceCommon


@tagged('post_install', '-at_install')
class TestCosts(EquipmentMaintenanceCommon):

    def test_labour_rate_from_employee_hourly_cost(self):
        request = self._create_request()
        activity = self._add_activity(request, hours=2, technician=self.technician_a)
        self.assertEqual(activity.labour_rate, 1500.0)
        self.assertEqual(activity.cost, 3000.0)

    def test_labour_rate_fallback_to_company_rate(self):
        request = self._create_request()
        activity = self._add_activity(request, hours=2, technician=self.technician_b)
        self.assertEqual(activity.labour_rate, 1000.0)
        self.assertEqual(activity.cost, 2000.0)

    def test_labour_rate_can_be_overridden(self):
        request = self._create_request()
        activity = self._add_activity(request, hours=2, labour_rate=800.0)
        self.assertEqual(activity.labour_rate, 800.0)
        self.assertEqual(activity.cost, 1600.0)

    def test_spare_part_cost_defaults_from_product(self):
        request = self._create_request()
        line = self._add_spare_part(request, quantity=3)
        self.assertEqual(line.unit_cost, 200.0)
        self.assertEqual(line.total_cost, 600.0)
        self.assertEqual(line.name, self.product_bearing.display_name)
        line.unit_cost = 250.0
        self.assertEqual(line.total_cost, 750.0)

    def test_request_cost_totals(self):
        request = self._create_request()
        self._add_activity(request, hours=2, technician=self.technician_a)   # 3000
        self._add_activity(request, hours=1, technician=self.technician_b)   # 1000
        self._add_spare_part(request, product=self.product_bearing, quantity=2)  # 400
        self._add_spare_part(request, product=self.product_oil, quantity=4)      # 200
        self.assertEqual(request.total_hours, 3.0)
        self.assertEqual(request.labour_cost, 4000.0)
        self.assertEqual(request.spare_part_cost, 600.0)
        self.assertEqual(request.total_cost, 4600.0)

    def test_totals_follow_line_changes(self):
        request = self._create_request()
        activity = self._add_activity(request, hours=2, technician=self.technician_a)
        part = self._add_spare_part(request, quantity=1)
        self.assertEqual(request.total_cost, 3200.0)
        activity.hours_spent = 4
        part.quantity = 2
        self.assertEqual(request.total_cost, 6400.0)
        part.unlink()
        self.assertEqual(request.spare_part_cost, 0.0)
        self.assertEqual(request.total_cost, 6000.0)

    def test_equipment_total_counts_completed_only(self):
        done = self._run_to_in_progress(self._create_request())
        self._add_activity(done, hours=1, technician=self.technician_a)  # 1500
        done.action_complete()
        running = self._run_to_in_progress(self._create_request())
        self._add_activity(running, hours=1, technician=self.technician_a)
        self.assertEqual(self.equipment.total_maintenance_cost, 1500.0)
        self.assertEqual(self.equipment.last_maintenance_date, done.date_done.date())

    def test_hours_must_be_positive(self):
        request = self._create_request()
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self._add_activity(request, hours=0)
            self.env.flush_all()

    def test_hours_max_per_line(self):
        request = self._create_request()
        with self.assertRaises(ValidationError):
            self._add_activity(request, hours=25)

    def test_quantity_must_be_positive(self):
        request = self._create_request()
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self._add_spare_part(request, quantity=-1)
            self.env.flush_all()

    def test_activity_default_technician_from_request(self):
        request = self._create_request(technician_id=self.technician_b.id)
        activity = self.env['equipment.maintenance.activity'].with_context(
            default_request_id=request.id).create({'request_id': request.id, 'name': 'Check'})
        self.assertEqual(activity.technician_id, self.technician_b)
