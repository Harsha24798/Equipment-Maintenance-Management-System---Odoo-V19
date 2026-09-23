from odoo import fields, models
from odoo.tools import SQL

from ..models.equipment_maintenance_request import (
    PRIORITIES,
    REQUEST_STATES,
    REQUEST_TYPES,
)


class EquipmentMaintenanceCostReport(models.Model):
    """Read-only reporting model backed by a SQL view: one row per maintenance
    request with its labour, spare part and total cost. Used by the pivot and
    graph views of the "Maintenance Cost Analysis" report."""
    _name = 'equipment.maintenance.cost.report'
    _description = 'Maintenance Cost Analysis'
    # _auto = False: the ORM does not create a table; rows come from _table_query
    _auto = False
    _rec_name = 'request_id'
    _order = 'request_date desc'

    # Dimensions (group by) - every field is readonly because the model is a SQL view
    request_id = fields.Many2one('equipment.maintenance.request', string='Request', readonly=True)
    equipment_id = fields.Many2one('equipment.maintenance.equipment', string='Equipment', readonly=True)
    category_id = fields.Many2one('equipment.maintenance.category', string='Category', readonly=True)
    location_id = fields.Many2one('equipment.maintenance.location', string='Location', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Responsible Employee', readonly=True)
    technician_id = fields.Many2one('res.users', string='Technician', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    request_type = fields.Selection(REQUEST_TYPES, string='Request Type', readonly=True)
    priority = fields.Selection(PRIORITIES, string='Priority', readonly=True)
    state = fields.Selection(REQUEST_STATES, string='Status', readonly=True)
    request_date = fields.Date(string='Request Date', readonly=True)
    date_done = fields.Datetime(string='Completed On', readonly=True)
    # Measures (summed in pivot / graph thanks to aggregator='sum')
    request_count = fields.Integer(string='# Requests', readonly=True, aggregator='sum')
    total_hours = fields.Float(string='Hours Spent', readonly=True, aggregator='sum')
    labour_cost = fields.Monetary(string='Labour Cost', readonly=True, aggregator='sum')
    spare_part_cost = fields.Monetary(string='Spare Part Cost', readonly=True, aggregator='sum')
    total_cost = fields.Monetary(string='Total Cost', readonly=True, aggregator='sum')

    # _table_query (Odoo 19): the SQL SELECT that provides the rows of this model.
    # One row per maintenance request, joined with its equipment (category,
    # location, responsible) and company (currency). id must be unique.
    # SQL(...) wraps the query so Odoo can compose it safely.
    @property
    def _table_query(self):
        return SQL("""
            SELECT
                r.id AS id,
                r.id AS request_id,
                r.equipment_id AS equipment_id,
                e.category_id AS category_id,
                e.location_id AS location_id,
                e.employee_id AS employee_id,
                r.technician_id AS technician_id,
                r.company_id AS company_id,
                c.currency_id AS currency_id,
                r.request_type AS request_type,
                r.priority AS priority,
                r.state AS state,
                r.request_date AS request_date,
                r.date_done AS date_done,
                1 AS request_count,
                COALESCE(r.total_hours, 0) AS total_hours,
                COALESCE(r.labour_cost, 0) AS labour_cost,
                COALESCE(r.spare_part_cost, 0) AS spare_part_cost,
                COALESCE(r.total_cost, 0) AS total_cost
            FROM equipment_maintenance_request r
            JOIN equipment_maintenance_equipment e ON e.id = r.equipment_id
            JOIN res_company c ON c.id = r.company_id
        """)
