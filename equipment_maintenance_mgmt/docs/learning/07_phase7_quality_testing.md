# Phase 7: Quality, Tests & Documentation

> Day 3 · ~3 h · Outcome: proof that the module works (automated tests, static checks, lint) and the deliverables (README, TECHNICAL, evidence).

## 1. LEARN

### 1.1 Odoo test framework
- `TransactionCase`: every test runs in a transaction that is **rolled back**, so tests are independent.
- `setUpClass` creates shared fixtures **once** per class (fast).
- `@tagged('post_install', '-at_install')` runs the tests after all modules are installed, the recommended setting for business tests.
- `with_user(user)` runs code as a given user, to test ACLs and record rules.
- `Form(model)` simulates the web form, including defaults and computes.
- `self.assertRaises(UserError | ValidationError | AccessError | IntegrityError)`.
- `new_test_user(env, login=..., groups='xmlid,xmlid')` is the helper from `odoo.tests.common`.
- SQL constraints raise at **flush**: call `self.env.flush_all()` inside `assertRaises(IntegrityError)` together with `mute_logger('odoo.sql_db')`.

Run:
```
odoo-bin -c odoo.conf -d test_maint -i equipment_maintenance_mgmt --test-enable ^
         --test-tags /equipment_maintenance_mgmt --stop-after-init --log-level=test
```

### 1.2 Static quality tools (no server needed)
| Tool | Command | What it proves |
|---|---|---|
| **ruff** with Odoo's own config | `ruff check --config "D:\Odoo Server\V19\server\ruff.toml" .` | Odoo core lint rules (`I001` isort is advisory per Odoo's config comment) |
| **ruff** PEP8 set | `ruff check --select E,W,F,B,N --line-length 120 .` | PEP8, pyflakes, bugbear, naming |
| **static_check.py** | `python docs/tools/static_check.py` | manifest ↔ files, every XML ref (internal and against the Odoo source), every view field exists on its model, Python XML-ID refs |

`static_check.py` was **mutation-tested**: an injected wrong field and a wrong group were both reported.

## 2. DESIGN: test strategy

| Layer | Test file | # tests |
|---|---|---|
| Master data rules (+ warranty cron) | `test_equipment.py` | 12 |
| Workflow, business guards, onchange, Many2many | `test_request_workflow.py` | 20 |
| Cost engine | `test_costs.py` | 11 |
| Security (ACL + rules + assigned-technician rule) | `test_security.py` | 11 |
| Reports (SQL view + QWeb) | `test_reports.py` | 5 |

The fixtures (`tests/common.py`) cover a technician **with** an employee hourly cost (1 500), a technician **without** one (company rate 1 000), a manager, master data and helpers (`_create_request`, `_add_activity`, `_add_spare_part`).

## 3. BUILD
- `tests/` holds the 6 files above.
- `README.md` is for functional readers; `TECHNICAL.md` is for developers.
- `docs/` is this learning pack.

## 4. VERIFY: your checklist
- [ ] `ruff` (both configurations): *All checks passed!*
- [ ] `python docs/tools/static_check.py` prints `OK: 11 models, 265 XML IDs, all references and view fields resolved.`
- [ ] Fresh DB **with demo**: install, no ERROR/WARNING for the module in the log.
- [ ] Fresh DB **without demo**: install works (the module does not depend on demo records).
- [ ] Upgrade (`-u equipment_maintenance_mgmt`) works.
- [ ] Test run: `0 failed, 0 error(s)`. Save the log to `docs/evidence/test_run.log`.
- [ ] Screenshots in `docs/evidence/`: see [testing/test_plan.md](../testing/test_plan.md) §4.

## 5. REFLECT
| Pitfall | Lesson |
|---|---|
| Tests that depend on demo data | Create fixtures in `setUpClass`; tests pass on any DB |
| Checking only the happy path | Most bugs are in the refusals: test every guard |
| Testing security as admin | Admin bypasses rules; always `with_user(technician)` |
| Counting chatter messages | Tracking adds messages; assert on content instead |

**Check yourself**
1. Why does `test_technician_cannot_read_other_request` use `read()` and not `search()`?
2. Why must `flush_all()` be inside the `assertRaises` block for SQL constraints?
