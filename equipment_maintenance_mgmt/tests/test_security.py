from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import EquipmentMaintenanceCommon


@tagged('post_install', '-at_install')
class TestSecurity(EquipmentMaintenanceCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_a = cls._create_request(technician_id=cls.technician_a.id)
        cls.request_b = cls._create_request(technician_id=cls.technician_b.id)

    def test_technician_sees_only_own_requests(self):
        request_model = self.env['equipment.maintenance.request'].with_user(self.technician_a)
        visible = request_model.search([('id', 'in', (self.request_a | self.request_b).ids)])
        self.assertEqual(visible, self.request_a)

    @mute_logger('odoo.addons.base.models.ir_rule')
    def test_technician_cannot_read_other_request(self):
        with self.assertRaises(AccessError):
            self.request_b.with_user(self.technician_a).read(['name'])

    def test_technician_can_report_request(self):
        # A technician reporting a request keeps access to it (create_uid rule)
        request = self.env['equipment.maintenance.request'].with_user(self.technician_b).create({
            'equipment_id': self.equipment.id,
        })
        self.assertEqual(request.state, 'new')
        request.with_user(self.technician_b).read(['name'])

    def test_technician_works_on_own_request(self):
        request = self.request_a.with_user(self.technician_a)
        request.action_start()
        self.env['equipment.maintenance.activity'].with_user(self.technician_a).create({
            'request_id': request.id,
            'name': 'Repair',
            'hours_spent': 1,
        })
        request.action_complete()
        self.assertEqual(request.state, 'completed')
        # the employee hourly cost is read through sudo, not exposed to the technician
        self.assertEqual(request.labour_cost, 1500.0)

    def test_only_assigned_technician_processes_request(self):
        # Technician B reports a request for Technician A: B can see it
        # (create_uid rule) but cannot start / complete work assigned to A.
        request = self.env['equipment.maintenance.request'].with_user(self.technician_b).create({
            'equipment_id': self.equipment.id,
            'technician_id': self.technician_a.id,
        })
        with self.assertRaises(UserError):
            request.with_user(self.technician_b).action_start()
        request.with_user(self.technician_a).action_start()
        self.assertEqual(request.state, 'in_progress')

    @mute_logger('odoo.addons.base.models.ir_model')
    def test_technician_cannot_delete_request(self):
        with self.assertRaises(AccessError):
            self.request_a.with_user(self.technician_a).unlink()

    @mute_logger('odoo.addons.base.models.ir_model')
    def test_technician_cannot_manage_equipment(self):
        with self.assertRaises(AccessError):
            self.env['equipment.maintenance.equipment'].with_user(self.technician_a).create({
                'name': 'Forbidden',
                'serial_no': 'NOPE-1',
                'category_id': self.category.id,
            })
        with self.assertRaises(AccessError):
            self.equipment.with_user(self.technician_a).write({'name': 'Renamed'})

    @mute_logger('odoo.addons.base.models.ir_rule')
    def test_technician_cannot_touch_lines_of_other_request(self):
        with self.assertRaises(AccessError):
            self.env['equipment.maintenance.activity'].with_user(self.technician_a).create({
                'request_id': self.request_b.id,
                'name': 'Not mine',
                'hours_spent': 1,
            })

    @mute_logger('odoo.addons.base.models.ir_model')
    def test_technician_cannot_read_cost_report(self):
        with self.assertRaises(AccessError):
            self.env['equipment.maintenance.cost.report'].with_user(self.technician_a).search([])

    def test_manager_sees_everything(self):
        request_model = self.env['equipment.maintenance.request'].with_user(self.manager)
        visible = request_model.search([('id', 'in', (self.request_a | self.request_b).ids)])
        self.assertEqual(visible, self.request_a | self.request_b)
        self.request_b.with_user(self.manager).action_cancel()
        self.request_b.with_user(self.manager).unlink()
        self.assertFalse(self.request_b.exists())

    def test_technician_domain(self):
        domain = self.env['equipment.maintenance.request']._default_technician_domain()
        technicians = self.env['res.users'].search(domain)
        self.assertIn(self.technician_a, technicians)
        self.assertIn(self.manager, technicians)  # manager implies technician
