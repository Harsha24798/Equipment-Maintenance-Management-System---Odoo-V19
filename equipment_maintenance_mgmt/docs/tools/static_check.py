"""Static consistency checker for equipment_maintenance_mgmt (no Odoo server needed).

Checks:
  * every file listed in the manifest exists and every module data file is listed
  * every XML ``ref``/``ref()``/``%(xmlid)d`` points to an XML ID defined in the
    module, or to an XML ID that exists in the Odoo source (for other modules)
  * every ``<field name="...">`` used in a view exists on the view's model
    (including fields of sub-views of One2many fields)
  * Python ``env.ref('equipment_maintenance_mgmt.xxx')`` / ``_for_xml_id`` targets exist

Usage:
    python docs/tools/static_check.py [ODOO_ADDONS_PATH]
"""
import ast
import contextlib
import pathlib
import re
import sys

from lxml import etree

MODULE = 'equipment_maintenance_mgmt'
ROOT = pathlib.Path(__file__).resolve().parents[2]
ODOO_ADDONS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else r'D:\Odoo Server\V19\server\odoo\addons')

# Fields brought by inherited Odoo models/mixins (not declared in this module)
MIXIN_FIELDS = {
    'mail.thread': {'message_ids', 'message_follower_ids', 'message_partner_ids',
                    'message_is_follower', 'message_needaction', 'message_attachment_count',
                    'has_message', 'message_has_error'},
    'mail.activity.mixin': {'activity_ids', 'activity_state', 'activity_user_id',
                            'activity_type_id', 'activity_date_deadline', 'my_activity_date_deadline',
                            'activity_summary', 'activity_exception_decoration'},
    'image.mixin': {'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128'},
}
BASE_FIELDS = {'id', 'display_name', 'create_uid', 'create_date', 'write_uid', 'write_date'}
# Fields of standard models referenced in our views
EXTERNAL_MODEL_FIELDS = {
    'res.config.settings': None,  # inherited view: fields checked against our extension only
}

errors = []


def error(msg):
    errors.append(msg)


# --------------------------------------------------------------------------
# 1. Python models -> fields
# --------------------------------------------------------------------------
models = {}      # model name -> set(fields)
inherits = {}    # model name -> list(inherited names)
for py in ROOT.rglob('*.py'):
    if 'docs' in py.parts or 'tests' in py.parts:
        continue
    tree = ast.parse(py.read_text(encoding='utf-8'))
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        name, parents, fields = None, [], set()
        for stmt in cls.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                target = stmt.targets[0].id
                if target == '_name' and isinstance(stmt.value, ast.Constant):
                    name = stmt.value.value
                elif target == '_inherit':
                    val = ast.literal_eval(stmt.value)
                    parents = [val] if isinstance(val, str) else list(val)
                elif (isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute)
                      and isinstance(stmt.value.func.value, ast.Name) and stmt.value.func.value.id == 'fields'):
                    fields.add(target)
        name = name or (parents[0] if parents else None)
        if name:
            models.setdefault(name, set()).update(fields)
            inherits.setdefault(name, [])
            inherits[name] += [p for p in parents if p != name]


def model_fields(model):
    result = set(BASE_FIELDS) | models.get(model, set())
    for parent in inherits.get(model, []):
        result |= MIXIN_FIELDS.get(parent, set()) | model_fields(parent)
    return result


# comodel of relational fields, parsed from source text: name = fields.One2many('model', ...)
comodels = {}
for py in ROOT.rglob('*.py'):
    if 'docs' in py.parts:
        continue
    text = py.read_text(encoding='utf-8')
    for cls_match in re.finditer(r"_name = '([a-z_.]+)'(.*?)(?=\nclass |\Z)", text, re.S):
        relational_re = r"\n    (\w+) = fields\.(?:One2many|Many2many|Many2one)\(\s*'([a-z_.]+)'"
        for fm in re.finditer(relational_re, cls_match.group(2)):
            comodels[cls_match.group(1), fm.group(1)] = fm.group(2)

# --------------------------------------------------------------------------
# 2. Manifest files
# --------------------------------------------------------------------------
manifest = ast.literal_eval((ROOT / '__manifest__.py').read_text(encoding='utf-8'))
listed = manifest['data'] + manifest.get('demo', [])
for rel in listed:
    if not (ROOT / rel).exists():
        error(f'manifest: missing file {rel}')
for data_file in list(ROOT.glob('*/*.xml')) + list(ROOT.glob('security/*.csv')):
    rel = data_file.relative_to(ROOT).as_posix()
    if rel.split('/')[0] in ('docs', 'static', 'tests'):
        continue
    if rel not in listed:
        error(f'manifest: file not listed {rel}')

# --------------------------------------------------------------------------
# 3. XML IDs defined in the module (in manifest order) and references
# --------------------------------------------------------------------------
defined = set()
for model in models:
    defined.add('model_' + model.replace('.', '_'))
for model, fields in models.items():
    for f in fields:
        defined.add(f"field_{model.replace('.', '_')}__{f}")

external_cache = {}


def external_exists(xmlid):
    module, _, ident = xmlid.partition('.')
    if module not in external_cache:
        ids = set()
        mod_dir = ODOO_ADDONS / module
        for f in list(mod_dir.rglob('*.xml')) + list(mod_dir.rglob('*.csv')):
            txt = f.read_text(encoding='utf-8', errors='ignore')
            ids.update(re.findall(r'id="([\w.]+)"', txt))
            ids.update(re.findall(r'^([\w]+),', txt, re.M))
        if module == 'base':
            ids.update({'user_root', 'user_admin', 'main_company', 'group_user', 'group_system',
                        'group_multi_company', 'group_no_one', 'module_category_supply_chain'})
        external_cache[module] = ids
    return ident in external_cache[module] or ident.startswith('model_')


def check_ref(xmlid, where):
    if '.' in xmlid:
        module, _, ident = xmlid.partition('.')
        if module == MODULE:
            if ident not in defined:
                error(f'{where}: undefined ref {xmlid}')
        elif not external_exists(xmlid):
            error(f'{where}: unknown external ref {xmlid}')
    elif xmlid not in defined:
        error(f'{where}: ref used before definition or undefined: {xmlid}')


REF_IN_EVAL = re.compile(r"ref\('([\w.]+)'\)")
for rel in listed:
    path = ROOT / rel
    if path.suffix == '.csv':
        for line in path.read_text(encoding='utf-8').splitlines()[1:]:
            cols = line.split(',')
            defined.add(cols[0])
            check_ref(cols[2], rel)
            if cols[3]:
                check_ref(cols[3], rel)
        continue
    doc = etree.parse(str(path))
    for el in doc.iter():
        if not isinstance(el.tag, str):
            continue
        for attr in ('ref', 'inherit_id', 'parent', 'action', 'web_icon_data'):
            val = el.get(attr)
            if val and attr != 'web_icon_data':
                check_ref(val, f'{rel}:{el.sourceline}')
        if el.get('groups'):
            for grp in el.get('groups').replace('!', '').split(','):
                check_ref(grp.strip(), f'{rel}:{el.sourceline} groups')
        for attr in ('eval', 't-call'):
            val = el.get(attr) or ''
            for m in REF_IN_EVAL.finditer(val):
                check_ref(m.group(1), f'{rel}:{el.sourceline}')
        if el.get('t-call') and el.get('t-call').startswith(MODULE):
            check_ref(el.get('t-call'), f'{rel}:{el.sourceline} t-call')
        if el.tag in ('record', 'template', 'menuitem') and el.get('id'):
            defined.add(el.get('id'))

# --------------------------------------------------------------------------
# 4. View fields exist on the model
# --------------------------------------------------------------------------


def check_arch(node, model, where):
    for child in node:
        if not isinstance(child.tag, str):
            continue
        if child.tag == 'field':
            fname = child.get('name')
            if fname not in model_fields(model):
                error(f'{where}:{child.sourceline} field {fname!r} not on {model}')
            comodel = comodels.get((model, fname))
            if comodel and len(child):
                check_arch(child, comodel, where)
            continue
        check_arch(child, model, where)


for rel in listed:
    path = ROOT / rel
    if path.suffix != '.xml':
        continue
    doc = etree.parse(str(path))
    for rec in doc.iter('record'):
        if rec.get('model') != 'ir.ui.view':
            continue
        model_el = rec.find("field[@name='model']")
        arch = rec.find("field[@name='arch']")
        if model_el is None or arch is None:
            continue
        model = model_el.text
        if model == 'res.config.settings':
            for f in arch.iter('field'):
                if f is arch:
                    continue
                if f.get('name') not in models.get('res.config.settings', set()):
                    error(f'{rel}:{f.sourceline} settings field {f.get("name")} not declared')
            continue
        check_arch(arch, model, rel)
    # search/filter domains referencing fields: best effort
    for rec in doc.iter('record'):
        if rec.get('model') == 'ir.actions.act_window':
            res_model = rec.find("field[@name='res_model']").text
            if res_model not in models:
                error(f'{rel}:{rec.sourceline} action res_model {res_model} unknown')

# --------------------------------------------------------------------------
# 5. Python references to module XML IDs
# --------------------------------------------------------------------------
for py in ROOT.rglob('*.py'):
    if 'docs' in py.parts:
        continue
    for m in re.finditer(rf"'{MODULE}\.(\w+)'", py.read_text(encoding='utf-8')):
        if m.group(1) not in defined:
            error(f'{py.relative_to(ROOT)}: python ref {MODULE}.{m.group(1)} undefined')

# --------------------------------------------------------------------------
# 6. <record> fields and selection values against the real model definitions
#    (this module + every module of its dependency tree in the Odoo source)
# --------------------------------------------------------------------------


def dependency_closure(depends):
    seen, todo = set(), list(depends) + ['base']
    while todo:
        mod = todo.pop()
        if mod in seen:
            continue
        seen.add(mod)
        manifest_path = ODOO_ADDONS / mod / '__manifest__.py'
        if manifest_path.exists():
            todo += ast.literal_eval(manifest_path.read_text(encoding='utf-8')).get('depends', [])
    return seen


def selection_values(call, constants):
    """Literal values of a fields.Selection(...) call, or None if dynamic."""
    arg = call.args[0] if call.args else None
    for kw in call.keywords:
        if kw.arg in ('selection', 'selection_add'):
            arg = kw.value
    if isinstance(arg, ast.Name):
        arg = constants.get(arg.id)
    if not isinstance(arg, ast.List):
        return None
    values = set()
    for item in arg.elts:
        if isinstance(item, ast.Tuple) and item.elts and isinstance(item.elts[0], ast.Constant):
            values.add(item.elts[0].value)
    return values


model_defs = {}   # model -> {'fields': {name: set|None}, 'parents': set()}
source_files = [py for py in ROOT.rglob('*.py') if not {'docs', 'tests'} & set(py.parts)]
for mod in dependency_closure(manifest['depends']):
    source_files += [py for py in (ODOO_ADDONS / mod).rglob('*.py') if 'tests' not in py.parts]
for py in source_files:
    try:
        tree = ast.parse(py.read_text(encoding='utf-8', errors='ignore'))
    except SyntaxError:
        continue
    constants = {t.id: node.value for node in tree.body if isinstance(node, ast.Assign)
                 for t in node.targets if isinstance(t, ast.Name)}
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        attrs, fields = {}, {}
        for stmt in cls.body:
            if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)):
                continue
            target, value = stmt.targets[0].id, stmt.value
            if target in ('_name', '_inherit', '_inherits'):
                with contextlib.suppress(ValueError):  # non-literal values are ignored
                    attrs[target] = ast.literal_eval(value)
            elif (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                  and isinstance(value.func.value, ast.Name) and value.func.value.id == 'fields'):
                fields[target] = selection_values(value, constants) if value.func.attr == 'Selection' else None
        inherit = attrs.get('_inherit') or []
        inherit = [inherit] if isinstance(inherit, str) else list(inherit)
        name = attrs.get('_name') or (inherit[0] if inherit else None)
        if not isinstance(name, str):
            continue
        entry = model_defs.setdefault(name, {'fields': {}, 'parents': set()})
        for fname, values in fields.items():
            known = entry['fields'].get(fname)
            entry['fields'][fname] = (known | values) if (known and values) else (values or known)
        entry['parents'] |= {p for p in inherit if p != name} | set(attrs.get('_inherits', {}) or {})


def all_fields(model, _seen=None):
    _seen = _seen or set()
    if model in _seen or model not in model_defs:
        return {}
    _seen.add(model)
    result = {}
    for parent in model_defs[model]['parents']:
        result.update(all_fields(parent, _seen))
    result.update(model_defs[model]['fields'])
    return result


for rel in listed:
    path = ROOT / rel
    if path.suffix != '.xml':
        continue
    for rec in etree.parse(str(path)).iter('record'):
        model = rec.get('model')
        known_fields = all_fields(model)
        if not known_fields:
            error(f'{rel}:{rec.sourceline} model {model!r} not found in module or Odoo source')
            continue
        for field_el in rec.findall('field'):
            fname = field_el.get('name')
            if fname not in known_fields and fname not in BASE_FIELDS:
                error(f'{rel}:{field_el.sourceline} field {fname!r} does not exist on {model}')
                continue
            values = known_fields.get(fname)
            text = (field_el.text or '').strip()
            if values and text and not field_el.get('eval') and not field_el.get('ref') and text not in values:
                error(f'{rel}:{field_el.sourceline} {model}.{fname} = {text!r} is not one of {sorted(values)}')

if errors:
    print(f'{len(errors)} problem(s):')  # ruff: ignore[print]
    for e in errors:
        print('  -', e)  # ruff: ignore[print]
    sys.exit(1)
print(f'OK: {len(models)} models, {len(defined)} XML IDs, all references and view fields resolved.')  # ruff: ignore[print]
