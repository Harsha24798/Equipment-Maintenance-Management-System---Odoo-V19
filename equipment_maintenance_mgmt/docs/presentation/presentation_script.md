# Presentation Script (≈ 25 min + Q&A)

Presenter: **Harsha Madushan** · Topic: *Equipment Maintenance Management, an Odoo 19 custom addon*

Visual assets:
- `static/description/banner.png` (title slide)
- `docs/assets/icon_256.png`
- the Mermaid diagrams in `TECHNICAL.md` and `docs/business/business_flow.md` (render them in VS Code or GitHub, or export them as images)

---

## Slide 1: Title (30 s)
Banner image. "Equipment Maintenance Management: an installable Odoo 19 application. I built it in 8 phases, each run as a learning cycle."

## Slide 2: The business problem (1.5 min)
- Assets break, requests get lost, costs are not traced to assets, and warranties expire unnoticed.
- Goal: register equipment → manage requests → capture labour and parts → know the cost → decide.

## Slide 3: Scope from the brief (1 min)
The 6 functional requirements and the technical expectations. Show the mapping table from `business_flow.md §7`: *every line is covered*.

## Slide 4: Approach: phases and the learning cycle (1.5 min)
Learn → Design → Build → Verify → Reflect, over 8 phases (show the phase map from `docs/README.md`).

"Before coding each phase, I checked the Odoo 19 documentation (Context7) and the Odoo 19 source code on my machine. Odoo 19 changed several APIs, so I verified each one."

## Slide 5: Architecture (2 min)
- Dependencies: base, mail, hr, hr_hourly_cost, product. Explain *why* each is needed.
- ER diagram (TECHNICAL §2): Category / Location / Employee → Equipment → Request → Activities + Spare parts; SQL-view cost report.
- File layout follows the Odoo coding guidelines.

## Slide 6: Equipment master (2 min)
- Fields from the brief plus extras.
- Validations: unique serial (SQL constraint, **`models.Constraint` in Odoo 19**), dates (`@api.constrains`).
- Warranty status: *non-stored* compute (depends on today) **with a search method**, so it still works in filters.
- Live: kanban badges, "Warranty Expiring Soon" filter.

## Slide 7: Request workflow (3 min)
- State diagram. Transitions declared once in `ALLOWED_TRANSITIONS` and guarded in Python (not only hidden buttons).
- Sequence in `create()` (no numbers lost), `@api.model_create_multi`.
- Setting a technician auto-assigns and plans a to-do. Completion needs an activity. Only new or cancelled requests can be deleted (`@api.ondelete`).
- Live: Act 2 of the demo script.

## Slide 8: Cost engine (3 min)
- The formula and dependency chain (TECHNICAL §3.2).
- Editable stored computes (`compute + store + readonly=False + precompute`) replace onchange.
- Labour rate from the employee hourly cost (**`sudo()` because HR restricts it**), with a company fallback.
- AbstractModel mixin: locking rules written once for both line types.
- Worked example: 8 000 + 3 000 + 3 400 = **14 400**.

## Slide 9: Security (2.5 min)
- 4 layers: groups → ACL → record rules → UI.
- **Odoo 19 privileges** (`res.groups.privilege`), `user_ids`, `all_group_ids`.
- Matrix: a technician sees only their assigned or reported requests; a manager sees all; companies are isolated.
- Live: Kasun vs Dilani side by side.

## Slide 10: Reporting (2.5 min)
- Cost analysis: SQL-view model with `_table_query` (Odoo 19 style) → pivot and graph.
- Pending maintenance: grouped by technician, overdue in red, PDF summary.
- Equipment history: PDF with all jobs, activities, parts and totals. Work order PDF.
- Live: pivot → graph → print history.

## Slide 11: Automation and UX (1 min)
2 daily crons (overdue, warranty), to-dos, empty-state help, default filters, settings screen, and a generated app icon.

## Slide 12: Quality (2 min)
- **59 automated tests** in 5 classes (equipment, workflow, costs, security, reports), including `with_user` security tests.
- Lint: Odoo's own ruff config + PEP8 set: clean.
- My `static_check.py` checks every XML reference and view field against the models and the Odoo source, with no server needed.
- Evidence: install log, test log, screenshots (see `docs/evidence/`).

## Slide 13: Odoo 19 lessons learned (1 min)
Top 6 from `coding/odoo19_changes.md`:
- `models.Constraint`
- privileges and `user_ids`
- `self.env._` with named placeholders
- `Domain` and `NotImplemented` in search methods
- `aggregator`
- `_table_query`

## Slide 14: Summary and next steps (30 s)
All requirements delivered and documented. Possible next steps:
- stock moves for spare parts (`stock` integration)
- preventive maintenance plans (recurring requests)
- a portal for requesters
- equipment QR codes

---

## Likely questions and answers

| Question | Answer |
|---|---|
| Why not extend Odoo's `maintenance` app? | The evaluation assesses ORM, views and security skills, so a standalone module shows them fully and avoids coupling. The technical name avoids any clash. |
| Why is the technician a user, not an employee? | Record rules and activities work with users, and technicians log in. The hourly cost still comes from the user's employee. |
| Why is `warranty_state` not stored? | It depends on today's date, so a stored value would be stale the next day. The search method keeps it filterable. |
| Why are costs stored? | To sum them in lists, group them in pivots, read them from the SQL view, and track changes. |
| What if a technician edits a completed job? | The view is readonly and, more importantly, the model raises a `UserError` in create, write and unlink of lines. |
| How do you stop technicians seeing other jobs? | Record rule `technician_id = user OR create_uid = user`, applied to lines through `request_id`; tested with `with_user`. |
| Why `sudo()`? Isn't that dangerous? | It is used once, only to read the numeric hourly cost that defaults the rate; the technician never gets HR data. It is documented in code. |
| Why `_table_query` instead of a DB view? | Odoo 19 supports it natively. There is no view to drop or recreate on upgrade, and it is the same pattern as core reports. |
| What happens on module upgrade to user changes? | Rules, sequence and categories are `noupdate`, so they are preserved. Views and menus are updated. |
| Multi-company? | `company_id` on all models, `check_company`, global company rules, sequence taken `with_company`. |
| How did you verify without a running server? | Static checks (syntax, references, view fields against the models and the Odoo source), plus lint. Tests and screenshots are run on the local Odoo 19 server. |
