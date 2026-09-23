# Live Demo Script (≈ 12 minutes)

Prerequisite: a database created **with demo data** and the module installed.

| Login | Password | Role |
|---|---|---|
| `admin` | (your admin password) | Manager + Settings |
| `dilani` | `dilani` | Maintenance Manager |
| `kasun` | `kasun` | Technician (hourly cost 1 500) |
| `nimal` | `nimal` | Senior Technician (hourly cost 2 000) |

> Tip: use one normal and one private browser window to show the manager and technician side by side.

---

## Act 1: Equipment master (manager, 2 min)
1. Log in as **dilani**, open the **Equipment Maintenance** app (point out the icon).
2. **Equipment** kanban. Point out the warranty badges:
   - *Diesel Generator*: **Expiring Soon** (20 days)
   - *File Server*: **Expired**
   - *CNC Lathe*: **Under Warranty**
3. Filter **Warranty Expiring Soon**, then group by **Category**.
4. Open **CNC Lathe Machine**:
   - smart buttons *Open / All Requests* and *Maintenance Cost* (14 400)
   - the Maintenance History tab and the chatter
5. Try to change the serial number to `HP-2021-0457` → **error: serial must be unique**.
6. Set the purchase date to tomorrow → **validation error**.

## Act 2: Request workflow (manager → technician, 4 min)
1. On *Forklift 3T*, click **New Request**: type *Corrective*, priority ★★★, scheduled date = today + 1, description "Hydraulic leak".
2. Save → number **MR/2026/000xx**, state **New**.
3. Click **Assign** without a technician → **"Please select a technician"**.
4. Select **Kasun** and **save** → state jumps to **Assigned**. The chatter shows a *Maintenance To-Do* for Kasun.
5. Switch to **kasun**'s window:
   - *My Requests* shows only Kasun's jobs (not Nimal's CNC calibration)
   - the Activities systray shows the new to-do
6. Kasun opens the request → **Start** → **In Progress**.
7. Click **Complete** straight away → **"Record at least one maintenance activity"**.
8. Activities tab: "Replace hose", 2 h → rate **1 500** (from his employee), cost **3 000**.
9. Spare Parts tab: *Hydraulic Oil (1L)* × 3 → unit cost **1 800** (product cost), total **5 400**.
10. Costs group: Labour **3 000** + Parts **5 400** = **8 400**.
11. **Complete** → green ribbon. Try to edit a line → locked.
12. Kasun selects the request in the list → *Actions* has **no Delete** (technicians have no delete right).

## Act 3: Security (1 min)
- Kasun opens *Equipment* and tries to edit → read-only (no Edit or New button).
- Kasun has **no Reporting or Configuration** menus.

## Act 4: Reports (manager, 3 min)
1. **Reporting > Maintenance Cost Analysis** (pivot): categories × months. Switch to the **graph** (stacked bars), then group by **Technician**.
2. **Reporting > Pending Maintenance**: grouped by technician; the *Hydraulic Press* request is **red** (overdue). Select all → *Print > Pending Maintenance Summary*.
3. **Equipment > CNC Lathe > Print History**: PDF with every request, its activities, parts and the grand total.
4. On a request → **Print** → work order with signature lines.

## Act 5: Automation and settings (1 min)
1. *Configuration > Settings*: Default Labour Rate and Warranty Alert days.
2. (Developer mode) *Settings > Technical > Scheduled Actions > "Equipment Maintenance: warranty expiry reminder" > Run Manually* → a *Warranty Expiry* activity appears on the Diesel Generator for Nimal.

## Closing (30 s)
"Every requirement of the brief is covered: equipment master, numbered requests with the full workflow, activities, spare parts, automatic costs, three reports, two security groups with record rules, validations, 59 automated tests, and README/TECHNICAL documentation."
