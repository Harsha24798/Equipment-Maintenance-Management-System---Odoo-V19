from odoo.tests import tagged

from .common import EquipmentMaintenanceCommon


@tagged('post_install', '-at_install')
class TestReports(EquipmentMaintenanceCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request = cls._create_request(technician_id=cls.technician_a.id)
        cls.request.action_start()
        cls._add_activity(cls.request, hours=2, technician=cls.technician_a)  # 3000
        cls._add_spare_part(cls.request, quantity=2)                          # 400
        cls.request.action_complete()

    def test_cost_report_matches_request(self):
        self.env.flush_all()
        line = self.env['equipment.maintenance.cost.report'].search(
            [('request_id', '=', self.request.id)])
        self.assertEqual(len(line), 1)
        self.assertEqual(line.labour_cost, 3000.0)
        self.assertEqual(line.spare_part_cost, 400.0)
        self.assertEqual(line.total_cost, 3400.0)
        self.assertEqual(line.category_id, self.category)
        self.assertEqual(line.state, 'completed')

    def test_cost_report_grouping(self):
        self.env.flush_all()
        groups = self.env['equipment.maintenance.cost.report']._read_group(
            [('equipment_id', '=', self.equipment.id)], ['category_id'], ['total_cost:sum'])
        self.assertEqual(groups, [(self.category, 3400.0)])

    def test_render_work_order(self):
        html, _format = self.env['ir.actions.report']._render_qweb_html(
            'equipment_maintenance_mgmt.equipment_maintenance_request_action_report',
            self.request.ids)
        self.assertIn(self.request.name.encode(), html)

    def test_render_equipment_history(self):
        html, _format = self.env['ir.actions.report']._render_qweb_html(
            'equipment_maintenance_mgmt.equipment_maintenance_equipment_action_report_history',
            self.equipment.ids)
        self.assertIn(b'Test Lathe', html)
        self.assertIn(self.request.name.encode(), html)

    def test_render_pending_report(self):
        pending = self._create_request()
        html, _format = self.env['ir.actions.report']._render_qweb_html(
            'equipment_maintenance_mgmt.equipment_maintenance_request_action_report_pending',
            (pending | self.request).ids)
        self.assertIn(pending.name.encode(), html)
        self.assertNotIn(self.request.name.encode(), html)  # completed: not pending
