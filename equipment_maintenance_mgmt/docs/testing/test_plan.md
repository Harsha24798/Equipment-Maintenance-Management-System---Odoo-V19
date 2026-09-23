# Test Plan & Evidence

## 1. How to run the automated tests

```
"D:\Odoo Server\V19\python\python.exe" "D:\Odoo Server\V19\server\odoo-bin" ^
  -c "D:\Odoo Server\V19\server\odoo.conf" ^
  --addons-path="D:\Odoo Server\V19\server\odoo\addons,C:\Users\Centrics\Desktop\Final Assestment" ^
  -d maint_test -i equipment_maintenance_mgmt --test-enable ^
  --test-tags /equipment_maintenance_mgmt --stop-after-init --http-port=8069 ^
  --logfile="C:\Users\Centrics\Desktop\Final Assestment\equipment_maintenance_mgmt\docs\evidence\test_run.log"
```
Then search the log for `failed` / `error`. The expected summary line is `0 failed, 0 error(s) of 59 tests`.

> The tests create their own data, so they pass with or without demo data. Use a throwaway database.

## 2. Automated test map (59 tests)

### `test_equipment.py` (12)
| Test | Proves |
|---|---|
| `test_display_name_includes_serial` | "Name [Serial]" |
| `test_name_search_by_serial_number` | search by serial in many2one |
| `test_serial_number_unique_per_company` | SQL constraint |
| `test_purchase_date_not_in_future` | `_check_dates` |
| `test_warranty_after_purchase` | `_check_dates` |
| `test_warranty_state_compute` | none / expired / expiring / valid |
| `test_warranty_state_search` | `=`, `!=` on non-stored field |
| `test_request_counters` | all / open counters |
| `test_copy_keeps_serial_unique` | copy_data "(copy)" |
| `test_category_equipment_count` | `_read_group` count |
| `test_cron_warranty_expiry_reminder` | warranty reminder for the responsible user, created once (idempotent) |
| `test_location_complete_name_and_recursion` | hierarchy + `_has_cycle` |

### `test_request_workflow.py` (20)
| Test | Proves |
|---|---|
| `test_sequence_number` | MR/ prefix, unique |
| `test_form_create` | UI-like creation, related fields |
| `test_create_with_technician_is_assigned` | auto-assign + to-do for the right user |
| `test_setting_technician_assigns_request` | write override |
| `test_assign_requires_technician` | guard |
| `test_full_workflow` | new → assigned → in progress → completed, dates, to-do closed |
| `test_invalid_transitions` | state machine refusals |
| `test_complete_requires_activity` | guard |
| `test_cancel_and_reset` | cancel removes the to-do; reset clears the technician |
| `test_cannot_cancel_completed` | guard |
| `test_unlink_rules` | delete new OK, running refused |
| `test_lines_locked_after_completion` | create / write / unlink of lines refused |
| `test_scheduled_date_after_request_date` | constraint |
| `test_no_request_on_archived_equipment` | constraint |
| `test_overdue` | compute + search + cancel |
| `test_duration` | stored duration |
| `test_tags_many2many` | Many2many link / unlink, inverse side |
| `test_onchange_equipment_warnings` | onchange warning: duplicate open request + warranty |
| `test_technician_required_when_assigned` | technician cannot be cleared on an assigned request |
| `test_cron_overdue_posts_message` | cron posts a note and notifies the technician |

### `test_costs.py` (11)
| Test | Proves |
|---|---|
| `test_labour_rate_from_employee_hourly_cost` | 2 h × 1 500 = 3 000 |
| `test_labour_rate_fallback_to_company_rate` | 2 h × 1 000 = 2 000 |
| `test_labour_rate_can_be_overridden` | 2 h × 800 = 1 600 |
| `test_spare_part_cost_defaults_from_product` | 3 × 200 = 600, override 750 |
| `test_request_cost_totals` | 4 000 + 600 = 4 600 |
| `test_totals_follow_line_changes` | recompute on edit / delete |
| `test_equipment_total_counts_completed_only` | rollup + last maintenance date |
| `test_hours_must_be_positive` | SQL CHECK |
| `test_hours_max_per_line` | ≤ 24 h |
| `test_quantity_must_be_positive` | SQL CHECK |
| `test_activity_default_technician_from_request` | default technician |

### `test_security.py` (11)
| Test | Proves |
|---|---|
| `test_technician_sees_only_own_requests` | record rule on search |
| `test_technician_cannot_read_other_request` | record rule on read → AccessError |
| `test_technician_can_report_request` | create + `create_uid` rule |
| `test_technician_works_on_own_request` | full job as technician; HR rate via sudo |
| `test_only_assigned_technician_processes_request` | a reporter cannot start work assigned to someone else |
| `test_technician_cannot_delete_request` | ACL |
| `test_technician_cannot_manage_equipment` | ACL create / write |
| `test_technician_cannot_touch_lines_of_other_request` | line rules |
| `test_technician_cannot_read_cost_report` | report ACL |
| `test_manager_sees_everything` | manager rule, cancel + delete |
| `test_technician_domain` | technician selection includes managers |

### `test_reports.py` (5)
| Test | Proves |
|---|---|
| `test_cost_report_matches_request` | SQL view values |
| `test_cost_report_grouping` | aggregation by category |
| `test_render_work_order` | QWeb PDF template renders |
| `test_render_equipment_history` | QWeb renders, includes requests |
| `test_render_pending_report` | only open requests printed |

## 3. Manual test cases (UI)

Log in with the demo users (see [business/demo_script.md](../business/demo_script.md)).

| # | Role | Steps | Expected | ✔ |
|---|---|---|---|---|
| M01 | Manager | Install the module on a new DB with demo | No error; app icon on home | ☐ |
| M02 | Manager | Equipment > New, all fields, save | Record created; chatter logs creation | ☐ |
| M03 | Manager | Duplicate serial number | Error "serial number must be unique per company" | ☐ |
| M04 | Manager | Purchase date = tomorrow | Validation error | ☐ |
| M05 | Manager | Warranty expiry before purchase | Validation error | ☐ |
| M06 | Manager | Filter "Warranty Expiring Soon" | Diesel Generator listed | ☐ |
| M07 | Manager | New request from equipment | Equipment prefilled; number MR/YYYY/xxxxx on save | ☐ |
| M08 | Manager | Click Assign without technician | Error "select a technician" | ☐ |
| M09 | Manager | Select technician, save | State Assigned; to-do in chatter | ☐ |
| M10 | Technician | My Requests | Only own requests visible | ☐ |
| M11 | Technician | Start → Complete without activity | Error "record at least one activity" | ☐ |
| M12 | Technician | Add activity 2 h | Rate from employee; cost = 2 × rate | ☐ |
| M13 | Technician | Add spare part × 3 | Unit cost = product cost; total = 3 × cost | ☐ |
| M14 | Technician | Check Costs group | Labour + Parts = Total | ☐ |
| M15 | Technician | Complete | Completed ribbon; lines readonly | ☐ |
| M16 | Technician | Try to edit equipment | Read-only | ☐ |
| M17 | Technician | Look for Reporting / Configuration menu | Not visible | ☐ |
| M18 | Manager | Cancel a request, then Reset to New | New, technician cleared | ☐ |
| M19 | Manager | Delete an in-progress request | Error "only new or cancelled" | ☐ |
| M20 | Manager | Reporting > Cost Analysis (pivot, graph) | Totals per category / month | ☐ |
| M21 | Manager | Reporting > Pending Maintenance | Grouped by technician; overdue red | ☐ |
| M22 | Manager | Print Pending Maintenance Summary | PDF lists only open requests | ☐ |
| M23 | Manager | Equipment > Print History | PDF with requests, lines, totals | ☐ |
| M24 | Manager | Request > Print | Work order PDF | ☐ |
| M25 | Admin | Settings: change Default Labour Rate | New activities (technician without hourly cost) use it | ☐ |
| M26 | Admin | Run the warranty cron manually | Warranty Expiry activity on Diesel Generator | ☐ |
| M27 | Admin | Run the overdue cron manually | Note on the Hydraulic Press request | ☐ |
| M28 | Admin | `-u equipment_maintenance_mgmt` | Upgrade without error | ☐ |

## 4. Evidence checklist (`docs/evidence/`)

| File | Content |
|---|---|
| `01_install_log.txt` | install log (no ERROR / WARNING) |
| `02_test_run.log` | test log with `0 failed, 0 error(s)` |
| `03_app_icon.png` | home screen with the app icon |
| `04_equipment_kanban.png` / `05_equipment_form.png` | warranty badges, smart buttons |
| `06_validation_serial.png` | unique serial error |
| `07_request_new.png` … `10_request_completed.png` | workflow steps, costs |
| `11_technician_my_requests.png` | record rule effect |
| `12_cost_pivot.png` / `13_cost_graph.png` | cost analysis |
| `14_pending_report.png` | pending grouped by technician |
| `15_history_pdf.pdf` / `16_work_order.pdf` / `17_pending_summary.pdf` | PDFs |
| `18_user_privilege.png` | user form with the "Equipment Maintenance" privilege |
| `19_static_check.txt` / `20_ruff.txt` | static check and lint output |

## 5. Static checks (already run during development)

| Check | Result |
|---|---|
| Python syntax (all files, `ast`) | ✔ 0 errors |
| XML well-formedness (all files, `lxml`) | ✔ 0 errors |
| `docs/tools/static_check.py` | ✔ `OK: 11 models, 265 XML IDs, all references and view fields resolved.` |
| ruff with Odoo `server/ruff.toml` (I001 advisory) | ✔ All checks passed |
| ruff PEP8 set (E, W, F, B, N) | ✔ All checks passed |
