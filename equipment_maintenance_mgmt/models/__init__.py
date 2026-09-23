# Import order matters: a model must be loaded before the models that
# _inherit from it (the line mixin is imported before activity / spare part)
from . import res_company
from . import res_config_settings
from . import equipment_maintenance_category
from . import equipment_maintenance_location
from . import equipment_maintenance_equipment
from . import equipment_maintenance_request
from . import equipment_maintenance_tag
from . import equipment_maintenance_line_mixin
from . import equipment_maintenance_activity
from . import equipment_maintenance_spare_part
