from datetime import timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tests import Form, tagged

from .common import EquipmentMaintenanceCommon


@tagged('post_install', '-at_install')
class TestRequestWorkflow(EquipmentMaintenanceCommon):

    def test_sequence_number(self):
        request_1 = self._create_request()
        request_2 = self._create_request()
        self.assertTrue(request_1.name.startswith('MR/'))
        self.assertNotEqual(request_1.name, request_2.name)
        self.assertEqual(request_1.state, 'new')

    def test_form_create(self):
        with Form(self.env['equipment.maintenance.request']) as form:
            form.equipment_id = self.equipment
            form.request_type = 'preventive'
        request = form.save()
        self.assertEqual(request.category_id, self.category)
        self.assertEqual(request.location_id, self.location)

    def test_create_with_technician_is_assigned(self):
        request = self._create_request(technician_id=self.technician_a.id)
        self.assertEqual(request.state, 'assigned')
        todo = self.env.ref('equipment_maintenance_mgmt.mail_activity_data_maintenance_todo')
        self.assertEqual(request.activity_ids.activity_type_id, todo)
        self.assertEqual(request.activity_ids.user_id, self.technician_a)

    def test_setting_technician_assigns_request(self):
        request = self._create_request()
        request.technician_id = self.technician_a
        self.assertEqual(request.state, 'assigned')

    def test_assign_requires_technician(self):
        request = self._create_request()
        with self.assertRaises(UserError):
            request.action_assign()

    def test_full_workflow(self):
        request = self._create_request()
        request.technician_id = self.technician_a
        request.action_start()
        self.assertEqual(request.state, 'in_progress')
        self.assertTrue(request.date_start)
        self._add_activity(request, hours=1.5)
        request.action_complete()
        self.assertEqual(request.state, 'completed')
        self.assertTrue(request.date_done)
        self.assertFalse(request.activity_ids, 'The to-do must be closed on completion')

    def test_invalid_transitions(self):
        request = self._create_request()
        with self.assertRaises(UserError):
            request.action_start()  # new -> in_progress not allowed
        with self.assertRaises(UserError):
            request.action_complete()  # new -> completed not allowed
        with self.assertRaises(UserError):
            request.action_reset_to_new()  # only from cancelled

    def test_complete_requires_activity(self):
        request = self._run_to_in_progress(self._create_request())
        with self.assertRaises(UserError):
            request.action_complete()

    def test_cancel_and_reset(self):
        request = self._create_request(technician_id=self.technician_a.id)
        request.action_cancel()
        self.assertEqual(request.state, 'cancelled')
        self.assertFalse(request.activity_ids)
        request.action_reset_to_new()
        self.assertEqual(request.state, 'new')
        self.assertFalse(request.technician_id)

    def test_cannot_cancel_completed(self):
        request = self._run_to_in_progress(self._create_request())
        self._add_activity(request)
        request.action_complete()
        with self.assertRaises(UserError):
            request.action_cancel()

    def test_unlink_rules(self):
        new_request = self._create_request()
        new_request.unlink()
        self.assertFalse(new_request.exists())
        running = self._run_to_in_progress(self._create_request())
        with self.assertRaises(UserError):
            running.unlink()

    def test_lines_locked_after_completion(self):
        request = self._run_to_in_progress(self._create_request())
        activity = self._add_activity(request)
        request.action_complete()
        with self.assertRaises(UserError):
            self._add_activity(request)
        with self.assertRaises(UserError):
            activity.hours_spent = 3
        with self.assertRaises(UserError):
            activity.unlink()
        with self.assertRaises(UserError):
            self._add_spare_part(request)

    def test_scheduled_date_after_request_date(self):
        with self.assertRaises(ValidationError):
            self._create_request(
                request_date=self.today,
                scheduled_date=self.today - timedelta(days=1))

    def test_no_request_on_archived_equipment(self):
        self.equipment.active = False
        with self.assertRaises(ValidationError):
            self._create_request()

    def test_overdue(self):
        request = self._create_request(
            request_date=self.today - timedelta(days=5),
            scheduled_date=self.today - timedelta(days=1))
        self.assertTrue(request.is_overdue)
        request_model = self.env['equipment.maintenance.request']
        self.assertIn(request, request_model.search([('is_overdue', '=', True)]))
        self.assertNotIn(request, request_model.search([('is_overdue', '=', False)]))
        request.action_cancel()
        self.assertFalse(request.is_overdue)

    def test_duration(self):
        request = self._run_to_in_progress(self._create_request())
        request.date_start = request.date_start - timedelta(hours=3)
        self._add_activity(request)
        request.action_complete()
        self.assertAlmostEqual(request.duration, 3.0, delta=0.05)

    def test_tags_many2many(self):
        tags = self.env['equipment.maintenance.tag'].create([{'name': 'Test Electrical'}, {'name': 'Test Safety'}])
        request = self._create_request(tag_ids=[Command.set(tags.ids)])
        self.assertEqual(request.tag_ids, tags)
        self.assertIn(request, tags[0].request_ids)
        request.tag_ids = [Command.unlink(tags[0].id)]
        self.assertEqual(request.tag_ids, tags[1])

    def test_onchange_equipment_warnings(self):
        existing = self._create_request()
        new_request = self.env['equipment.maintenance.request'].new({'equipment_id': self.equipment.id})
        result = new_request._onchange_equipment_id()
        self.assertIn(existing.name, result['warning']['message'])  # duplicate open request
        self.assertIn('warranty', result['warning']['message'])     # equipment under warranty

    def test_technician_required_when_assigned(self):
        request = self._create_request(technician_id=self.technician_a.id)
        with self.assertRaises(ValidationError):
            request.technician_id = False

    def test_cron_overdue_posts_message(self):
        request = self._create_request(
            technician_id=self.technician_a.id,
            request_date=self.today - timedelta(days=5),
            scheduled_date=self.today - timedelta(days=1))
        self.env['equipment.maintenance.request']._cron_overdue_requests()
        overdue_messages = request.message_ids.filtered(lambda m: 'overdue' in (m.body or ''))
        self.assertEqual(len(overdue_messages), 1)
        self.assertIn(self.technician_a.partner_id, overdue_messages.partner_ids)
