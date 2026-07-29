# MARTIQ compliance audit

Audit date: 2026-07-29  
Source of truth: the complete 71-section MARTIQ specification (`64a10dae-.../pasted-text.txt`) plus the 26-section audit protocol (`282b591f-.../pasted-text.txt`).  
Evidence rule: `VERIFIED_WORKING` is used only where an automated test, build, migration, or direct runtime call proves the complete applicable slice. A file existing by itself is not verification.

## Initial execution evidence

| Check | Initial result | Evidence |
|---|---|---|
| Backend automated tests | VERIFIED_WORKING | `python -m pytest -q`: 36 passed (2026-07-29 final re-audit) |
| Admin production compile | VERIFIED_WORKING | `npm run build`: Vite build completed, 1,637 modules |
| Mobile strict TypeScript | VERIFIED_WORKING | `npm run typecheck`: exit 0 |
| Expo dependency health | VERIFIED_WORKING | `npx expo-doctor`: 18/18 |
| Admin lint | VERIFIED_WORKING | `eslint src --max-warnings 0`; production build also passed |
| Mobile lint | VERIFIED_WORKING | ESLint and strict TypeScript passed; Android export passed |
| Clean PostgreSQL migration/seed | VERIFIED_WORKING | Docker PostgreSQL 16 healthy; migrations through `0009`, idempotent seed, and Alembic drift check passed |
| Browser visual/runtime test | BROKEN | No controllable browser session is available in the current environment |

## Requirement traceability matrix

Abbreviations: C = customer, S = staff, BA = branch admin, HO = head office, PA = platform admin. “Final” remains equal to the observed initial state until the repair and re-audit phase proves otherwise.

| ID | Specification section | Requirement | Role | Required UI | Backend / DB | Required test | Initial status | Evidence | Missing or broken | Final |
|---|---|---|---|---|---|---|---|---|---|---|
| R01 | 1–3 Product | Three sources in one detection-to-resolution workflow; honest AI positioning | All | Mobile/admin/docs | `Incident` | source integration | PARTIALLY_WORKING | `domain.py`, report/audit/vision tests | Manual entry source and full lifecycle absent | PARTIALLY_WORKING |
| R02 | 4 Stack | Expo, React/Vite, FastAPI, SQLAlchemy/Alembic/Postgres/OpenCV/OCR abstraction | All | all clients | full stack | build/start | PARTIALLY_WORKING | package files, requirements, compose | Optional YOLO person adapter requires local weights/runtime; OCR engine disabled by default | PARTIALLY_WORKING |
| R03 | 5 Repository | Separated monorepo, docs, demo videos, developer commands | Dev | n/a | n/a | clean setup | PARTIALLY_WORKING | repo tree, Makefile | `demo-videos` absent; no separate vision package | PARTIALLY_WORKING |
| R04 | 6 Roles | Five roles and role-specific experiences | All | role redirects/navigation | `Role`, RBAC | every role login/access | PARTIALLY_WORKING | `Role`, auth tests | Admin UI not role-tailored; PA/HO pages absent | PARTIALLY_WORKING |
| R05 | 7 Tenancy | Organisation and branch isolation in backend | All | scoped data | tenant FKs and filters | cross-tenant reads/writes | VERIFIED_WORKING | `test_security_media_reaudit.py`, `test_report_flow.py` | Broader endpoint matrix still desirable | VERIFIED_WORKING |
| R06 | 8 Navigation | Five customer tabs; central report choices | C | `BottomNav.tsx` | n/a | route integrity | PARTIALLY_WORKING | central Report button exists | Report bottom sheet/three choices absent | PARTIALLY_WORKING |
| R07 | 9 Home header | Greeting, market/branch, hours/open, notifications/avatar and selection | C | `/` | `/home`, `/branches` | runtime UI/API | PARTIALLY_WORKING | `app/index.tsx`, `GET /home` | Market/branch change persistence absent | PARTIALLY_WORKING |
| R08 | 9 Home search | Search, barcode, suggestions, recent searches | C | `/`, `/products`, `/scanner` | products API | UI flow | PARTIALLY_WORKING | search and scanner routes | Recent searches/suggestions not persisted | PARTIALLY_WORKING |
| R09 | 9 Home content | Dynamic news, quick actions, loyalty, discounts, reports, branches | C | `/` | `/home` | API/UI | PARTIALLY_WORKING | `index.tsx`, seeded API data | News detail navigation and full card semantics incomplete | PARTIALLY_WORKING |
| R10 | 10 Products | Search/filter/sort/detail, branch price/availability, favourite, mismatch report | C | `/products` | products/favourites/prices | CRUD and UI flow | PARTIALLY_WORKING | product/favourite endpoints/tests | Product detail route, sort, branch prices in UI absent | PARTIALLY_WORKING |
| R11 | 11 Discounts | Filters, campaign detail, dates/branches, favourite | C | prices/discount screens | `/discounts` campaigns | API/UI | BACKEND_ONLY | discount endpoint and seed | No dedicated customer discount/detail screen | BACKEND_ONLY |
| R12 | 12 Suggestions | Separate form, category, optional branch/image/anonymous, tracking/timeline | C/HO | `/suggestions`, admin | suggestion endpoints/model | E2E | PARTIALLY_WORKING | tested persistence/status | Image upload linking and detail timeline absent | PARTIALLY_WORKING |
| R13 | 13 Reports form | Market/branch/category/title/description/product/media/review/submit | C | `/report` | `POST /reports`, uploads | complete report E2E | PARTIALLY_WORKING | report integration tests | Stepper, product link, attachment binding/progress/retry absent | PARTIALLY_WORKING |
| R14 | 13 Tracking | Tracking number, list/detail/timeline, media/reasons/refresh | C | `/report-detail` | reports/history | E2E reload | PARTIALLY_WORKING | polling timeline works | Pull-to-refresh, media, rejection/resolution fields incomplete | PARTIALLY_WORKING |
| R15 | 14 Expiry | Barcode→photo→OCR candidates→manual confirmation→result→report prefill | C | `/scanner`, `/expiry` | OCR/image API | OCR/UI flow | PARTIALLY_WORKING | OCR parsing tests; camera flow | Report prefill absent; malformed date handling weak | PARTIALLY_WORKING |
| R16 | 15 Loyalty | Multiple demo cards, masked ID, code, balances, transactions, rewards, demo label | C | `/cards` | loyalty models/endpoints | API/UI | PARTIALLY_WORKING | cards/transactions API | Multiple cards, reward offers and code display incomplete | PARTIALLY_WORKING |
| R17 | 16 Profile | Edit/image/preferences/favourites/history/language/privacy/logout/delete | C | `/profile` | profile/delete APIs | mutation/session | PARTIALLY_WORKING | profile edit/logout | Menu rows inactive; image/preferences/delete UI absent | PARTIALLY_WORKING |
| R18 | 17 Staff home | Today/overdue/completed/re-audits/flags/findings/metrics | S | `/staff` | staff audit APIs | staff role UI | PARTIALLY_WORKING | staff-specific redirect and list | Re-audits, flags and metrics not surfaced | PARTIALLY_WORKING |
| R19 | 17 Staff audit | Start/scan/photo/OCR/condition/count/review/complete/incident | S | `/audit` | audit endpoints/models | E2E | PARTIALLY_WORKING | audit test creates finding incident | No camera/OCR integration in audit UI; no review step | PARTIALLY_WORKING |
| R20 | 18 Quality | Duration, duplicates, photos, dates, count, corrections, flags | S/Admin | audit views | `AuditQualityFlag` | abuse tests | PARTIALLY_WORKING | duplicate/flag tests | Duplicate-image and missing-photo checks incomplete | PARTIALLY_WORKING |
| R21 | 18 Re-audit | Selection, assignment, comparison, mismatch flag, score explanation | S/Admin | staff/admin audit | re-audit/score endpoints | consistency test | PARTIALLY_WORKING | mismatch test passes | Random auto-selection and full UI absent | PARTIALLY_WORKING |
| R22 | 19 Experimental | Clearly labelled optional smart audit and metrics docs | C | experiment entry | optional flag/metrics | independence | MISSING | no route | Experiment UI/measurement docs absent | MISSING |
| R23 | 20–21 Incident model | Sources/categories/priorities/departments/full statuses/history | Admin | incident pages | incident entities/service | valid/invalid transitions | PARTIALLY_WORKING | incident model and status tests | Enum/status metadata do not match full spec | PARTIALLY_WORKING |
| R24 | 20 Incident detail | Case media, source details, assignment, notes, timeline, SLA/actions | BA/HO | `/incidents/:id` | incident/attachment/history | UI/API | PARTIALLY_WORKING | operational case page | Attachment viewer, assignment entity, SLA, reject reason missing | PARTIALLY_WORKING |
| R25 | 22–28 Vision source | MP4 OpenCV, ROI rules, persistence, incident, clear/auto-resolve/reopen | Admin | `/cameras` | vision pipeline/models | controlled MP4 | VERIFIED_WORKING | `test_video_pipeline_mp4.py` | Controlled synthetic MP4 proves implemented deterministic rule | VERIFIED_WORKING |
| R26 | 22 Vision rules | Spill/hazard, blocked aisle, promo coverage; queue optional | Admin | camera rules/events | `CameraRule` | per-rule videos | VERIFIED_WORKING | rule-specific controlled videos and automated tests | OpenCV demos are controlled rules; optional queue YOLO requires real local weights | VERIFIED_WORKING |
| R27 | 24/67 Vision health | source active, last frame/event/error/FPS; safe disabled state | Admin | health/camera | health endpoints | failure smoke | VERIFIED_WORKING | `/health/vision`, `/admin/vision-health` | Per-rule engine, ROI, thresholds, state, timestamps, event, error and approximate FPS exposed | VERIFIED_WORKING |
| R28 | 29 Loss analytics | Phase 2, no accusation/identity recognition | n/a | docs only | none | non-presence | OUT_OF_SCOPE_BY_SPECIFICATION | product-scope docs | Correctly not core | OUT_OF_SCOPE_BY_SPECIFICATION |
| R29 | 30 Score | Explainable clamped score and factors | BA/HO | dashboard | score endpoint | formula tests | VERIFIED_WORKING | `test_auth_analytics_platform.py` | Formula is MVP simplified but explained | VERIFIED_WORKING |
| R30 | 31 Analytics | Operational metrics, breakdowns, ranking and filters | BA/HO | dashboards | analytics API | metric/filter tests | PARTIALLY_WORKING | dashboard and score endpoints | Most trends/breakdowns/filters absent | PARTIALLY_WORKING |
| R31 | 32 News CRUD | Create/edit/publish/unpublish/archive; mobile reflection | HO/PA/C | content/mobile | news endpoints/model | CRUD→mobile | PARTIALLY_WORKING | CRUD tests | Publish/unpublish/archive semantics incomplete | PARTIALLY_WORKING |
| R32 | 32 Product CRUD | Product/category/barcode/image/package/archive; mobile reflection | HO/PA/C | content/products | product endpoints/models | CRUD→mobile | PARTIALLY_WORKING | CRUD tests | Package size/archive/category CRUD absent | PARTIALLY_WORKING |
| R33 | 32 Price CRUD | Branch price, discounts, effective dates, mobile reflection | HO/PA/C | content/prices | price endpoint/model | CRUD→mobile | PARTIALLY_WORKING | create price endpoint | Update/delete/effective dates/UI reflection incomplete | PARTIALLY_WORKING |
| R34 | 32 Campaign CRUD | Products/branches/dates/status and mobile reflection | HO/PA/C | content/discounts | campaigns endpoints | CRUD→mobile | PARTIALLY_WORKING | campaign create/link/list | Update/deactivate/delete and full UI absent | PARTIALLY_WORKING |
| R35 | 32 Branch content | Details, coordinates/hours/services/contact/users/cameras/modules | HO/PA | branch pages | branch/service models | CRUD/security | PARTIALLY_WORKING | branch/service seed, platform create | Coordinates/contact/update/detail admin UI absent | PARTIALLY_WORKING |
| R36 | 32 Loyalty offers | Create/update/deactivate and mobile reflection | HO/PA/C | content/cards | offer model/API | CRUD→mobile | MISSING | only cards/transactions | Loyalty offer entity/API/UI absent | MISSING |
| R37 | 33 Database | Required normalised entities, FKs/indexes/timestamps/migrations | All | n/a | SQLAlchemy/Alembic | drift/migration | PARTIALLY_WORKING | two migrations, many models | Several named entities collapsed/absent; timestamp consistency gaps | PARTIALLY_WORKING |
| R38 | 34 Auth | Register/login/refresh/me/logout/change password | All | auth screens | auth APIs | auth tests | PARTIALLY_WORKING | login/refresh/me/register tested | Server logout/change-password absent | PARTIALLY_WORKING |
| R39 | 34 Markets | Organisations/branches/details/hours/services | C | selection/branch detail | market endpoints | tenant API/UI | PARTIALLY_WORKING | org/branch lists | Branch detail/service endpoint absent | PARTIALLY_WORKING |
| R40 | 34 Notifications | List/unread/mark read/all/preferences/types | C/S | `/notifications` | notifications API/model | state tests | PARTIALLY_WORKING | list/single-read | Mark-all/preferences absent | PARTIALLY_WORKING |
| R41 | 34 Platform | Organisation/branch/admin/module/settings/health/usage/log/reset | PA | platform dashboard | platform endpoints | PA-only tests | BACKEND_ONLY | create/list/usage endpoints | Most management/health/reset UI and APIs absent | BACKEND_ONLY |
| R42 | 35 Security | Hash/JWT/RBAC/tenant/branch/upload/CORS/secrets/rate/audit logs | All | safe errors | security layer | adversarial suite | PARTIALLY_WORKING | RBAC/tenant/upload tests | Rate-limit structure absent; demo defaults weak by design | PARTIALLY_WORKING |
| R43 | 35 Upload security | Size/MIME/signature/extension/name/traversal/access/missing/retry | All | upload UI | storage/FileAsset | security tests | PARTIALLY_WORKING | ownership/linking tests, safe storage service | Protected download endpoint and frontend retry absent | PARTIALLY_WORKING |
| R44 | 36 Privacy | No biometric identity/accusation; retention/access/deletion | All | privacy/settings | settings/delete request | policy/access tests | PARTIALLY_WORKING | no biometric code, deletion request | Retention enforcement and privacy UI absent | PARTIALLY_WORKING |
| R45 | 37–39 Business docs | Pricing, ROI method, competition, no invented claims | Business | docs | n/a | review | PARTIALLY_WORKING | product-scope docs | Dedicated complete sections need audit | PARTIALLY_WORKING |
| R46 | 40 Scope | CORE delivered; Phase 2/3/experiment separated | All | all | all | acceptance suite | PARTIALLY_WORKING | scope doc | Multiple CORE screens/endpoints incomplete | PARTIALLY_WORKING |
| R47 | 43 Demo accounts | All five accounts, documented non-production password | All | login | seed/users | each login/role | PARTIALLY_WORKING | seed and README | Full live login matrix pending | PARTIALLY_WORKING |
| R48 | 44 Demo data | 2 orgs, 3–5 branches, 20–30 products and all operational entities | All | all | seed | idempotency/counts | PARTIALLY_WORKING | 2 org/4 branch/24 product | Cameras/events/suggestions/flags not all seeded | PARTIALLY_WORKING |
| R49 | 45 Demo story | Customer→admin→staff→camera→HO coherent demo | All | all clients | all APIs | runtime E2E | PARTIALLY_WORKING | separate automated slices | Complete live story not yet observed | PARTIALLY_WORKING |
| R50 | 46 UX states | Loading/empty/error/success/confirm/skeleton/refresh/responsive | All | all | n/a | visual/runtime | PARTIALLY_WORKING | shared `State`, SafeArea | Skeletons, confirmations, refresh inconsistent | PARTIALLY_WORKING |
| R51 | 47/64 Localisation | Natural AZ and EN, switchable, no hard-coded labels | All | mobile/admin | language field | key/switch tests | UI_ONLY | `locales/az.ts`, `en.ts` | Components mostly hard-coded AZ; admin lacks i18n | UI_ONLY |
| R52 | 48 Error handling | Offline/API/token/upload/barcode/OCR/permission/duplicate/size | All | all flows | typed errors | failure tests | PARTIALLY_WORKING | selected errors handled | Offline, refresh failure, upload retry inconsistent | PARTIALLY_WORKING |
| R53 | 49 Observability | Structured logs and health/database/vision | Admin | health | middleware/endpoints | smoke | PARTIALLY_WORKING | request logging and three health endpoints | Event-specific structured logging incomplete | PARTIALLY_WORKING |
| R54 | 50 Acceptance | Six E2E flows and tenant/role security | All | all | all | runtime suite | PARTIALLY_WORKING | 16 integration tests cover major slices | Content/suggestion full E2E and role matrix incomplete | PARTIALLY_WORKING |
| R55 | 51 README | Full setup/env/demo/tests/limitations/roadmap | Dev | n/a | n/a | command verification | PARTIALLY_WORKING | README has start/test/limits | Architecture/demo video/reset/roadmap details incomplete | PARTIALLY_WORKING |
| R56 | 52 Environment | All required variables and no secrets | Dev | n/a | settings | config test | PARTIALLY_WORKING | `.env.example` lists variables | `VISION_VIDEO_PATH`, `OCR_ENGINE`, seed password not represented in Settings | PARTIALLY_WORKING |
| R57 | 53 Standards | Strict TS, typed Python, modular/reusable, no giant files | Dev | all | all | lint/type/build | PARTIALLY_WORKING | TS strict passes | Admin is giant `main.tsx`; lint missing | PARTIALLY_WORKING |
| R58 | 54 Limitations | Honest limitations documented and reflected in UI | All | relevant labels | feature flags | content review | PARTIALLY_WORKING | README/product scope | Some demo/simulated labels inconsistent | PARTIALLY_WORKING |
| R59 | 57–59 Design system | Reference-derived tokens and reusable components | All | mobile/admin | n/a | visual review | PARTIALLY_WORKING | token files, shared mobile UI | Component inventory only partly implemented | PARTIALLY_WORKING |
| R60 | 60 Customer inventory | 42 required customer screens and reachability | C | Expo routes | customer APIs | route/runtime | BROKEN | 15 customer-ish routes exist | Many routes/details/settings/onboarding absent | BROKEN |
| R61 | 61 Staff inventory | 15 staff screens and separated work navigation | S | Expo routes | audit APIs | route/runtime | BROKEN | staff + audit routes | Most dedicated screens absent | BROKEN |
| R62 | 62 Admin inventory | 35 admin pages and grouped role-aware navigation | BA/HO/PA | React routes | admin APIs | route/runtime | BROKEN | 7 routes exist | Most pages and role-specific panels absent | BROKEN |
| R63 | 63 Responsive/accessibility | Safe areas, dynamic widths, 44px targets, AA, keyboard/labels | All | all | n/a | device/axe/manual | PARTIALLY_WORKING | SafeArea and responsive CSS basics | Full accessibility audit not available/proven | PARTIALLY_WORKING |
| R64 | 65 Assets | Organised fictional product/news/branch/camera assets | All | cards/details | URLs/uploads | missing asset checks | MISSING | placeholder URLs referenced | Required asset directories/files absent | MISSING |
| R65 | 66 API/state | Central typed clients, refresh/error handling/query invalidation | Mobile/Admin | all | OpenAPI/API | contract tests | PARTIALLY_WORKING | central clients + React Query | Admin/mobile types partial; refresh handling incomplete | PARTIALLY_WORKING |
| R66 | 67 Feature flags | Vision/OCR/notifications/loyalty/map/experiment and honest fallback | All | unavailable state | config/settings | disabled-mode tests | PARTIALLY_WORKING | vision flag/manual OCR fallback | Several flags absent | PARTIALLY_WORKING |
| R67 | 68 Non-goals | No checkout/payment/biometrics/etc. | n/a | docs | none | non-presence | VERIFIED_WORKING | repository inspection | No prohibited major area found | VERIFIED_WORKING |
| R68 | 70 Customer UI DoD | Dynamic rich home, report, timelines, API content, states | C | customer routes | customer APIs | visual/E2E | PARTIALLY_WORKING | home dynamic, reports working | Screen depth/states/localisation incomplete | PARTIALLY_WORKING |
| R69 | 70 Staff UI DoD | Assigned audits, scan/progress/summary/flags, separated nav | S | staff routes | audit APIs | visual/E2E | PARTIALLY_WORKING | role redirect, tasks/progress | scan/photo/summary/flag UI incomplete | PARTIALLY_WORKING |
| R70 | 70 Admin UI DoD | Consistent dashboard/cases/comparison/score/responsive | BA/HO/PA | admin routes | admin APIs | visual/E2E | PARTIALLY_WORKING | sidebar/cards/case/score | Head-office/platform/comparison/details incomplete | PARTIALLY_WORKING |
| R71 | 71 Vertical milestones | Report slice, customer visual milestone, AI milestone | All | all | all | acceptance tests | PARTIALLY_WORKING | report and AI tests pass; home dynamic | Full visual milestone and live runtime observation incomplete | PARTIALLY_WORKING |

## Severity-ranked initial gaps

### BLOCKER

- The source specification calls for a complete CORE product, while 42 customer, 15 staff, and 35 admin screen inventories are not represented by reachable non-placeholder routes.
- Admin has no separate head-office or platform-admin experience, despite backend role support.
- Staff audit mobile UI does not perform the required camera/OCR-assisted capture flow.

### HIGH

- Full incident state model/transition metadata is narrower than the specification.
- Required customer discount/news/product detail and settings flows are incomplete.
- Content, analytics, platform management and branch-management CRUD are incomplete.
- Localisation files exist but most UI strings bypass them.
- Historical note: the original audit required PostgreSQL and demo-login revalidation. Subsequent runtime verification completed both against Docker PostgreSQL; the evidence below is retained as historical context only.

### MEDIUM

- Missing lint scripts and frontend route/translation integrity tests.
- Upload attachment binding, progress, protected retrieval and retry are incomplete.
- Feature flags, structured event logs, notification preferences, retention controls and demo reset are incomplete.

### LOW

- Python 3.13 reports timezone-naive `datetime.utcnow()` deprecation warnings.
- Generated admin build artifacts and local QA databases should be kept out of the source deliverable.

## Re-audit log

1. Clean migration/drift check: a new `compliance_migration.db` was upgraded through `0001` and `0002`; `alembic check` returned `No new upgrade operations detected`.
2. Seed idempotency: a new `compliance_seed.db` produced 2 organisations, 4 branches, 6 users and 24 products; the second seed run returned `Demo data already exists` without duplication.
3. Real HTTP smoke: Uvicorn ran on `127.0.0.1:8011`; `/health` returned `ok`; customer login returned role `CUSTOMER`; `/home` returned 3 news items, 24 products, 3 tenant branches and 1 report.
4. Authentication: all five demo roles now have an automated login → token → `/auth/me` → logout test; invalid password is rejected. Backend suite increased from 16 to 17 passing tests.
5. Customer report repair: `mobile/app/report.tsx` now requires an explicit category and branch, provides a three-step review flow, binds uploaded assets, displays upload/submission failures, and accepts product/barcode prefill.
6. Product-to-report repair: the previously inert price-mismatch action now opens the report flow with product name, barcode, category and description prefilled.
7. Notification repair: API and mobile UI now support mark-all-read in addition to individual read state.
8. Mobile revalidation: strict TypeScript passed and the Android production export bundled all 1,115 modules successfully.
9. Admin revalidation: production TypeScript/Vite build passed with 1,637 transformed modules.
10. Superseded environment note: Docker Desktop was unavailable during the original audit. It is now running PostgreSQL 16 on port 5432, and revisions through `0004` plus seed idempotency have been verified against that service.

Rows affected by these repairs: R13 and R38 improved but remain `PARTIALLY_WORKING` because their full specification surface is wider; R40 remains `PARTIALLY_WORKING` pending preferences; R47 is now `VERIFIED_WORKING` for login/session role evidence; R48 is `VERIFIED_WORKING` for the specified top-level counts and idempotency, while not every optional operational seed subtype exists.

### R60–R62 implementation pass — 2026-07-29

- R60 customer: added API-backed news detail, product detail with branch prices/availability, campaign list/detail, branch detail/services, persistent selected branch, interactive profile navigation, privacy/delete-request, and dedicated reports/settings routes. Home cards now navigate to details and use the persisted selected branch.
- R61 staff: replaced text-only audit entry with camera barcode scanning, expiry-photo capture, OCR candidates, manual correction tracking, condition selection, review, persisted photo reference and completion. Added staff quality summary and mobile re-audit result submission.
- R62 admin: login now persists the validated admin role. Branch Admin, Head Office and Platform navigation are separated; content routes are hidden from Branch Admin and platform tenant controls are limited to Platform Admin. Added analytics, product creation/catalogue management and platform organisation/usage pages.
- Direct contract tests now cover selected-branch tenant validation, branch detail/services, product branch pricing, campaign detail and staff quality summary.
- Revalidation: backend `19 passed`; mobile strict TypeScript passed; Android Expo export passed with 1,119 modules; admin production build passed with 1,638 modules.
- Honest remaining status: R60–R62 improve from `BROKEN` to `PARTIALLY_WORKING`, not `VERIFIED_WORKING`. Forgot-password/onboarding, server-persisted notification preferences, complete AZ/EN switching, all admin CRUD families, full branch/staff/camera configuration and browser/device click-through evidence remain open.

## Final release audit — 2026-07-29

This section supersedes earlier implementation-pass notes for the flows and gates explicitly re-tested below. `VERIFIED_WORKING` is used only where a real FastAPI process and a clean PostgreSQL 16 Docker database completed the story and the persisted result was read back. A route or successful compilation alone is not treated as runtime verification.

### Test environment and clean database evidence

- Docker service: `sabahhub-db-1`, image `postgres:16-alpine`, status `healthy`, published on `5432`.
- Isolated database: `martiq_release_qa`; it was dropped and recreated before the run.
- `python -m alembic upgrade head` applied revisions through `0007 (head)` using `PostgresqlImpl` and transactional DDL.
- First `python -m scripts.seed`: `Seeded 2 organisations, 4 branches and 30 products`.
- Second `python -m scripts.seed`: `Demo data already exists`.
- Post-seed counts: 2 organisations, 4 branches, 30 products and 6 users; the second run introduced no duplicates.
- FastAPI ran at `http://127.0.0.1:8000`; `GET /health` returned `{"status":"ok","service":"martiq-api"}`.
- Admin Vite ran at `http://127.0.0.1:5173`; an HTTP request returned status 200.
- All six seeded personas used during the stories authenticated against the live server: customer, staff, branch admin, head-office admin, platform admin and the second-tenant city admin. The five required demo identities were `customer@demo.az`, `staff@demo.az`, `branch@demo.az`, `head@demo.az`, and `platform@martiq.az`.

### CORE runtime stories

| Story | Screen route | Live API path(s) exercised | Persisted model(s) | Automated test evidence | Observed runtime result | Final status |
|---|---|---|---|---|---|---|
| Customer report lifecycle | `/products` → `/product-detail` → `/report` → `/report-detail`; admin `/branch/reports` and incident detail | `GET /api/v1/products`, `GET /api/v1/products/{id}`, `POST /api/v1/reports`, `PATCH /api/v1/admin/incidents/{id}`, `GET /api/v1/reports/{id}` | `Product`, `CustomerReport`, `Incident`, `IncidentStatusHistory` | `test_customer_admin_customer_report_flow`; lifecycle transition tests | A customer created a product-linked report. Branch admin advanced the same incident through PRECHECK, VERIFICATION_REQUIRED, VERIFIED, ASSIGNED, IN_PROGRESS, RESOLUTION_CANDIDATE and MANUALLY_RESOLVED. Customer read back `RESOLVED` with an 8-entry timeline. | `VERIFIED_WORKING` at API/database level |
| Management suggestion | `/suggestions` → `/suggestion-detail`; head-office suggestion workspace | `POST /api/v1/suggestions`, `PATCH /api/v1/admin/suggestions/{id}`, `GET /api/v1/suggestions/{id}` | `ManagementSuggestion`, `SuggestionStatusHistory`, `Notification` | `test_favourite_suggestion_and_admin_notification` | Customer submitted a suggestion; head office changed it to `PLANNED`; customer read the updated status from the live API. | `VERIFIED_WORKING` at API/database level |
| Head-office content propagation | Head-office news/product/price/campaign pages; customer `/news`, `/products`, `/discounts` | `POST /api/v1/admin/news`, `/admin/products`, `/admin/prices`, `/admin/campaigns`, `/admin/campaigns/{id}/products`; customer list endpoints | `News`, `Product`, `ProductPrice`, `DiscountCampaign`, `DiscountCampaignProduct` | `test_head_office_content_reflects_to_customer` | Newly created news, product, branch price and discount campaign were all returned to the customer by the running server. | `VERIFIED_WORKING` at API/database level |
| Staff camera-assisted audit | `/staff` → `/audit` | Staff audit list/start/barcode/item/complete endpoints and `POST /api/v1/ocr/image` | `AuditTask`, `AuditResultItem`, `AuditQualityFlag`, `Incident` | `test_staff_camera_audit_quality_and_incident` | Staff started a seeded task, resolved a barcode, sent an actual repository image to OCR, received the honestly labelled `manual-fallback` engine result, explicitly confirmed an expired item, completed the required count, and produced a `STAFF_AUDIT` incident visible to branch admin. | `VERIFIED_WORKING` for live API/database flow; physical-device camera interaction not directly observed |
| Camera persistence lifecycle | Admin camera/rule/event and incident routes | `POST /api/v1/admin/cameras`, camera-rule creation, `POST /api/v1/admin/camera-rules/{id}/process`, incident reopen | `Camera`, `CameraRule`, `CameraEvent`, `CameraClipMetadata`, `Incident` | `test_controlled_spill_segmentation_persists_stores_evidence_and_resolves` and camera false-alert/telemetry tests | The controlled spill video was processed by `OPENCV_HSV_SEGMENTATION`. Trigger persistence opened an incident, evidence metadata was stored, clear persistence moved it to `AUTO_RESOLVED`, and an admin then reopened it. | `VERIFIED_WORKING` for controlled MP4 processing; this is not claimed as RTSP or a custom YOLO spill model |
| Tenant and branch isolation | Role-specific admin routes | Tenant-scoped incident listing and incident mutation endpoints | `Organisation`, `Branch`, tenant/branch foreign keys on incident data | `test_cross_tenant_and_cross_branch_incidents_are_isolated`, `test_head_office_cannot_cross_organisation` | Second-tenant incident IDs and NOVA incident IDs were disjoint; branch-admin cross-branch mutation returned 404; customer access to admin incidents returned 403. | `VERIFIED_WORKING` |

The screen-route column records the implemented UI entry points, while the observed-result column records the independently executed HTTP/database story. Interactive browser click-through could not be captured because the audit environment reported `No browser is available`. The Expo Android bundle was produced, but no physical Android camera session was available. Consequently, visual rendering and device-camera ergonomics are not promoted to `VERIFIED_WORKING` by this audit.

### Release gates and exact outputs

```text
docker compose ps
sabahhub-db-1  postgres:16-alpine  ...  Up ... (healthy)  0.0.0.0:5432->5432/tcp

python -m alembic check
No new upgrade operations detected.

python -m pytest -q
................................. [100%]
33 passed, 94 warnings in 15.07s

python -m pytest -q tests/test_content_crud_upload.py::test_upload_validation tests/test_security_media_reaudit.py::test_uploaded_asset_is_linked_only_to_owners_report
.. [100%]
2 passed, 5 warnings in 3.07s

cd admin; npm run lint
eslint src --max-warnings 0
exit 0

cd admin; npm run build
1644 modules transformed
dist/assets/index-24CJ-q3N.js  282.00 kB | gzip: 86.45 kB
built in 3.82s

cd mobile; npm run check:i18n
Translation integrity passed: 237 AZ keys / 237 EN keys

cd mobile; npm run lint
eslint app components services constants locales --max-warnings 0
exit 0

cd mobile; npm run typecheck
tsc --noEmit
exit 0

cd mobile; npx expo-doctor
Running 18 checks on your project...
18/18 checks passed. No issues detected!

cd mobile; npx expo export --platform android
Android Bundled ... node_modules/expo-router/entry.js (1132 modules)
Exported: dist
```

The 94 backend warnings originate from `python-jose`, whose installed dependency still calls deprecated `datetime.utcnow()` internally. Repository application code uses timezone-aware UTC handling; the remaining warning is external dependency behaviour.

### Integrity checks

```text
Mobile routes: 14; missing: none
Admin route markers: 11; missing: none
OpenAPI paths: 105; required missing: none
```

The route check covered the CORE mobile routes, the three admin role prefixes and their relevant feature markers, and the live OpenAPI paths used by authentication, reports, suggestions, content, staff OCR/audits and camera processing. Upload security was executed separately against file-type validation and owner-only media binding, with both tests passing. Generated `admin/dist`, `mobile/dist`, caches and QA artifacts remained untracked; `git status --short` was empty before this document update.

### Approved post-release / external integration work only

- Live POS/ERP catalogue, price and stock synchronisation.
- Production loyalty-provider/card integration; the present flow is explicitly simulated.
- Production email/SMS delivery for password recovery and transactional notifications.
- Push-notification provider credentials and delivery infrastructure.
- Production object storage/CDN and retention policy integration.
- Maps/geocoding provider integration.
- RTSP/NVR camera connectivity and production deployment calibration.
- A production OCR service and any custom hazard model only after a labelled retail dataset, validated weights and measured accuracy are available.
- Approved Phase 2/3 advanced analytics, hardware pilots and model-operations work.

No unresolved CORE API/database failure was observed in this release audit. Interactive visual acceptance on a browser and physical Android camera acceptance remain release-environment evidence tasks, not claims of completed external integration.

### Architecture and admin hardening re-audit — 2026-07-29

- Migration `0008` separates universal customer selection into `users.selected_organisation_id` and `customer_market_memberships`; `/profile/preferred-market` no longer mutates tenant ownership in `users.organisation_id`.
- Direct PostgreSQL/HTTP evidence: switching the demo customer from Nova Market to CityMart left `organisation_id` unchanged, while `/home` returned CityMart and both Home loyalty and `/loyalty/cards` returned only the CityMart organisation ID.
- Admin browser `prompt()` usage is zero. Incident assignment/reject/resolve/reopen uses an accessible modal with department, SLA and reason fields; news/product/campaign editing uses modal forms; destructive content actions use a confirmation dialog.
- Head-office operational analytics now includes average/median resolution time, overdue/open totals, automatic/manual resolution, customer verification rate, re-audit consistency, recurring issues, source/status/category/hour breakdowns and branch/status/source/date filters.
- Platform management now supports organisation rename/activation and tenant administrator edit/deactivation through protected API endpoints and modal forms; migration `0009` adds organisation lifecycle state.
- Revalidation after these changes: backend `36 passed`; PostgreSQL Alembic upgraded through `0009`; `alembic check` returned no drift; admin lint/build and mobile lint/typecheck passed.
