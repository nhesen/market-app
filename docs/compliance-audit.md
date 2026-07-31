# MARTIQ current compliance audit

Audit date: 2026-07-31

Repository scope: current tree containing Alembic revisions through `0011_customer_companion.py`.

Evidence policy: `VERIFIED_WORKING` requires a current migration, automated test, build, direct HTTP/database observation, or a combination that proves the applicable slice. A file, route, rendered button, or historical result is not accepted by itself.

## Current release evidence

| Gate | Current result |
|---|---|
| Clean PostgreSQL migration | `0011 (head)` |
| Alembic drift | `No new upgrade operations detected.` |
| Seed idempotency | First run seeded 2 organisations, 4 branches and 30 products; second run reported existing demo data |
| Backend suite | `44 passed, 129 warnings in 28.71s` |
| Admin lint | ESLint exit 0, zero warnings |
| Admin production build | Vite 6.4.3, 1,729 modules, built in 3.57s |
| Admin JavaScript output | 423.95 kB, gzip 125.65 kB |
| Runtime database | Clean Docker PostgreSQL database `martiq_admin_final` |

The warnings are emitted by third-party `python-jose` calling deprecated `datetime.utcnow()`. Application-owned UTC helpers are timezone-aware.

## Admin gap analysis before 0010

The pre-change admin already had authentication, backend-enforced role boundaries, separate role layouts, unified incidents, content CRUD foundations, platform management, modal actions and a navy/teal design system. Direct inspection found these CORE gaps:

- no audit-template entity or usable admin template CRUD;
- no template-based admin assignment that appeared immediately in staff mobile;
- shallow audit result, re-audit and staff-quality views;
- quality flags could not be filtered or resolved;
- three inconsistent Smart Store Score formulae;
- analytics lacked priority filtering, critical/resolved-today/rate/audit/camera KPIs;
- no loyalty-offer admin CRUD;
- campaign products could be added only through an API with no complete interface;
- camera rules were telemetry-only and could not be safely configured;
- report detail did not expose or operate the linked incident;
- branch services were not editable;
- product barcode uniqueness was global rather than organisation-scoped;
- admin API sessions did not refresh access tokens;
- language switching reloaded the application;
- platform and several operational mutations did not consistently produce audit logs.

## Current admin verification matrix

| Area | Status | Current evidence |
|---|---|---|
| Three distinct role route trees | VERIFIED_WORKING | `/branch`, `/head`, `/platform`; backend role tests pass |
| Branch isolation | VERIFIED_WORKING | Live cross-branch mutation returned HTTP 404; automated boundary tests pass |
| Organisation isolation | VERIFIED_WORKING | Head-office scope tests pass; organisation filters are backend-side |
| Platform cross-tenant authority | VERIFIED_WORKING | Platform health/organisation/admin/module tests and live calls pass |
| Branch dashboard | VERIFIED_WORKING | Nine required KPI cards use backend analytics; incident/report/audit/camera sections use API data |
| Customer report list/detail | VERIFIED_WORKING | Backend search/category/subcategory/status/date filters, direct verify/reject and linked-incident navigation |
| Incident list/detail | VERIFIED_WORKING | Backend source/category/priority/status/department/overdue/date/search filters; backend allowed transitions drive actions |
| Incident assignment/SLA/notes | VERIFIED_WORKING | Canonical department dropdown, assignee validation, SLA, internal/customer notes and immutable timeline |
| Incident rejection/resolution/reopen | VERIFIED_WORKING | Mandatory reasons, modal confirmation, database transitions and tests |
| Suggestion lifecycle | VERIFIED_WORKING | Review/planned/implemented/rejected controls persist admin notes; rejection/implementation notes required in UI |
| Audit templates | VERIFIED_WORKING | `AuditTemplate`, migration, scoped CRUD interface and integration test |
| Audit assignment | VERIFIED_WORKING | Template/staff/due/priority/instructions form; assigned task observed in staff endpoint |
| Audit result detail | VERIFIED_WORKING | Items, barcode, date, OCR correction, condition, evidence reference, notes and quality flags |
| Quality flags | VERIFIED_WORKING | Staff/type/severity/resolution backend filters; resolve/reopen persistence and UI |
| Re-audit assignment | VERIFIED_WORKING | Original task, alternate staff and due time persist; complete original item set returned for comparison |
| Staff quality detail | VERIFIED_WORKING | Completion, duration, flags by type, consistency and explainable non-disciplinary score |
| Camera overview/rules | VERIFIED_WORKING | Engine/ROI/threshold/persistence/state/FPS/error plus safe threshold/persistence/enabled editing |
| Camera events | VERIFIED_WORKING | Evidence metadata, engine, score, linked incident and confirmed false-alert action |
| Head-office network dashboard | VERIFIED_WORKING | Twelve database-backed KPI cards, rankings, source/status/recurring charts |
| Operational analytics | VERIFIED_WORKING | Date/branch/source/category/priority/status backend filters and complete KPI response |
| Branch comparison | VERIFIED_WORKING | Score/open/critical/overdue/resolution/audit/camera quality columns |
| Smart Store Score | VERIFIED_WORKING | One canonical service used by branch detail, dashboard and network ranking; consistency test passes |
| News/product/category/price | VERIFIED_WORKING | Existing CRUD interfaces and content tests remain passing |
| Campaign products | VERIFIED_WORKING | List/add/delete interface persists product, branch and discount price links |
| Loyalty offers | VERIFIED_WORKING | RHF/Zod create/edit/delete; live offer appeared in customer endpoint |
| Branch settings/services | VERIFIED_WORKING | Name/address/hours/open/services persist with tenant/branch checks |
| Platform organisations/admins | VERIFIED_WORKING | Create/edit/activate/deactivate interfaces and role validation |
| Platform modules/health/usage/settings/logs/reset | VERIFIED_WORKING | Routes, confirmation UI, persistence, audit logs and platform-only tests |
| Product barcode tenancy | VERIFIED_WORKING | Revision 0010 changes uniqueness to `(organisation_id, barcode)` |
| Admin token refresh | VERIFIED_WORKING | Central API client refreshes once, stores rotated tokens and handles 401/403 consistently |
| Major new forms | VERIFIED_WORKING | Audit template, assignment, re-audit, loyalty and campaign-product forms use React Hook Form + Zod |
| Destructive confirmation | VERIFIED_WORKING | Incident/report/content/platform/camera high-impact actions use modal confirmation, not browser prompts |
| Responsive/accessibility foundation | VERIFIED_WORKING | Responsive layout, overflow tables, focus styles, labelled fields and accessible dialog roles compile |
| AZ/EN architecture | PARTIALLY_WORKING | Runtime switch no longer reloads; shared labels translate |

Admin localisation remains partial because several feature-page strings are still authored directly in Azerbaijani or mixed operational terminology. This is recorded honestly rather than marked complete from the existence of an i18n file.

The repository's browser-driven visual click-through could not be executed in this audit session because the browser-control runtime reported that no browser was available. Runtime API stories, lint and production compilation were completed, but they are not presented as a substitute for a real browser accessibility/responsive pass.

## Runtime flows — clean PostgreSQL

FastAPI was started against `martiq_admin_final`, a newly-created PostgreSQL Docker database migrated through 0010.

### Customer report lifecycle

```text
CUSTOMER_REPORT created
NEW -> PRECHECK -> VERIFIED
VERIFIED -> ASSIGNED (QUALITY_CONTROL, admin assignee, 24-hour SLA)
ASSIGNED -> IN_PROGRESS -> RESOLUTION_CANDIDATE -> MANUALLY_RESOLVED
customer report endpoint after transition: RESOLVED
```

### Audit administration

```text
branch admin created Runtime Dairy Audit template
branch admin assigned template to scoped STAFF member
assigned AuditTask persisted with template_id and due_at
staff /staff/audits endpoint immediately contained the task: true
```

### Head-office content

```text
head office created organisation-scoped loyalty offer
customer /loyalty/offers endpoint contained the created offer: true
automated tests cover content CRUD and campaign/price behaviour
```

### Tenant/platform

```text
branch admin mutation against CityMart branch: HTTP 404
platform /platform/health: HTTP 200
platform and admin mutations produced AuditLog records
```

## Exact commands

```powershell
docker compose up -d db
$env:DATABASE_URL='postgresql+psycopg://martiq:martiq@localhost:5432/martiq_admin_final'
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m scripts.seed
python -m scripts.seed
python -m pytest -q

cd ..\admin
npm run lint
npm run build
```

## Genuine external-dependency items

- Real RTSP ingestion remains a deployment integration; controlled MP4 is labelled as simulated input.
- Production push/email providers and third-party loyalty systems are not integrated.
- Production object storage/CDN and signed media delivery require deployment credentials and infrastructure.
- No custom retail-hazard model is claimed because no production labelled dataset or weights are supplied.

`npm audit --omit=dev` currently reports the upstream React Router RSC-mode advisory for the latest published `react-router-dom@7.18.2`. MARTIQ Admin is a client-only `BrowserRouter` SPA and does not enable React Server Components, server actions or React Router framework actions, so the vulnerable execution mode is not present. The dependency is kept on the latest published release and should be upgraded when the upstream package publishes a fixed version.

## Customer mobile final re-audit — 2026-07-31

Current PostgreSQL evidence used a newly-created `martiq_customer_final` database. Alembic migrated every revision from `0001` through `0011`; `alembic current` returned `0011 (head)` and `alembic check` returned `No new upgrade operations detected.` The first seed printed `Seeded 2 organisations, 4 branches and 30 products`; the second printed `Demo data already exists`.

Customer verification added direct coverage for published organisation news, selected-branch news, rejection of another branch/organisation, draft/archive/expired filtering, detail-scope enforcement, seed idempotency and authenticated owner media. The complete backend suite returned `44 passed, 129 warnings in 28.71s`.

Mobile commands returned:

```text
npm run typecheck       -> exit 0
npm run lint            -> exit 0
npm run check:i18n      -> Translation integrity passed: 325 AZ keys / 325 EN keys
npx expo-doctor         -> 18/18 checks passed
npx expo export --platform android -> Android bundle complete, 1,136 modules, 3.39 MB Hermes bundle
```

Real PostgreSQL runtime context switching returned `200` for both Nova Market and CityMart. Nova exposed 24 products, two current-market cards and eight branch-scoped visible news items; CityMart exposed six products, one current-market card and six visible news items. Database inventory was 13 Nova and six CityMart articles. `User.organisation_id` remained unchanged while `selected_organisation_id` persisted CityMart, proving that customer market context does not mutate account tenant ownership.

Physical-device camera quality, device Settings redirection and real GPS/map behaviour remain device/environment verification items. Android export proves bundling, not physical camera execution.
