# Learning Pack: Equipment Maintenance Management (Odoo 19)

**Author:** Harsha Madushan · **Module:** `equipment_maintenance_mgmt`

This folder is a complete learning and presentation pack for the module. It explains **what** was built, **why** (the business flow), and **how** (the Odoo 19 coding), one phase at a time. Every phase follows the same learning cycle.

```
 ┌────────┐   ┌────────┐   ┌───────┐   ┌────────┐   ┌─────────┐
 │ LEARN  │──►│ DESIGN │──►│ BUILD │──►│ VERIFY │──►│ REFLECT │──┐
 └────────┘   └────────┘   └───────┘   └────────┘   └─────────┘  │
      ▲                                                           │
      └───────────────────────── next phase ──────────────────────┘
```

## How to use this pack

| If you want to... | Read |
|---|---|
| Understand the business problem and flow | [business/business_flow.md](business/business_flow.md) |
| Learn Odoo 19 development step by step | [learning/](learning/): phases 0 → 7 in order |
| See the rules the code follows | [coding/coding_standards.md](coding/coding_standards.md) |
| Know what changed in Odoo 19 (with source proofs) | [coding/odoo19_changes.md](coding/odoo19_changes.md) |
| Walk through the code file by file | [coding/code_walkthrough.md](coding/code_walkthrough.md) |
| Present the project | [presentation/presentation_script.md](presentation/presentation_script.md) |
| Run a live demo | [business/demo_script.md](business/demo_script.md) |
| Test manually and collect evidence | [testing/test_plan.md](testing/test_plan.md) |

## Phase map (3 days × 8 h)

| # | Phase | Day | Effort | Learning focus | Document |
|---|---|---|---|---|---|
| 0 | Environment & module anatomy | 1 | 1.5 h | manifest, addons path, module structure | [00](learning/00_phase0_module_anatomy.md) |
| 1 | Master data | 1 | 3 h | fields, constraints, computed and searchable fields, mail.thread | [01](learning/01_phase1_master_data.md) |
| 2 | Maintenance request & workflow | 1–2 | 4 h | sequences, create/write overrides, state machine, header buttons | [02](learning/02_phase2_request_workflow.md) |
| 3 | Activities, spare parts & cost engine | 2 | 3 h | One2many lines, depends chains, Monetary, AbstractModel mixin | [03](learning/03_phase3_cost_engine.md) |
| 4 | Security | 2 | 2 h | Odoo 19 privileges, groups, ACL, record rules, sudo | [04](learning/04_phase4_security.md) |
| 5 | Reporting | 2–3 | 3.5 h | SQL-view models, pivot/graph, QWeb PDF | [05](learning/05_phase5_reporting.md) |
| 6 | Automation, data, icons & UX | 3 | 2.5 h | crons, activities, data/demo, noupdate, app icon | [06](learning/06_phase6_automation_ux.md) |
| 7 | Quality, tests & documentation | 3 | 3 h | TransactionCase, security tests, ruff, static checks | [07](learning/07_phase7_quality_testing.md) |
| | **Total** | | **22.5 h** (+1.5 h buffer) | | |

## Folder contents

```
docs/
├── README.md                      this index
├── learning/                      one document per phase (learning cycle)
├── business/
│   ├── business_flow.md           roles, processes, diagrams, cost example
│   └── demo_script.md             step-by-step live demo on demo data
├── coding/
│   ├── coding_standards.md        Odoo 19 coding guidelines applied (checklist)
│   ├── odoo19_changes.md          Odoo 19 differences, verified in source code
│   └── code_walkthrough.md        file-by-file explanation
├── presentation/
│   └── presentation_script.md     slide outline, talking points, likely Q&A
├── testing/
│   └── test_plan.md               automated tests map + manual test cases + evidence checklist
├── tools/
│   ├── static_check.py            server-less consistency checker (refs, view fields, manifest)
│   └── make_icons.py              generates icon.png / icon.svg / banner.png
├── assets/                        large icon for slides
└── evidence/                      put your screenshots and test logs here
```
