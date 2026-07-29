# MARTIQ current compliance audit

Audit date: 2026-07-29

Repository scope: current tree containing Alembic revisions `0008_customer_market_context.py` and `0009_platform_management.py`.

Evidence policy: `VERIFIED_WORKING` requires a current migration, automated test, build, direct HTTP/database observation, or a combination that proves the applicable slice. A file, route, rendered button, or old result is not accepted by itself.

## Executive result

The post-0009 release is functional at API/database and compile-time quality-gate level. A clean PostgreSQL database migrates to `0009 (head)`, the seed is idempotent, all 36 backend tests pass, all five roles complete the authentication lifecycle, admin and mobile quality gates pass, tenant/branch boundaries hold, and the new market context keeps customer selection separate from tenant ownership.

The audit did find and repair one release-blocking migration defect. On the first clean database, revision 0008 raised `DuplicateColumn: selected_organisation_id` because early migrations call current `Base.metadata.create_all()` and later migrations assumed their objects did not yet exist. Revisions 0008 and 0009 now inspect the current schema before adding those objects. A newly-created database was then migrated from zero successfully. This document records the repaired rerun, not the failed run as a success.

Direct visual click-through of the admin modals and physical-device camera/OCR flows was not possible because this environment exposed no controllable browser and no Android device. Those items remain partial where visual or hardware behaviour is material, even though their API actions, source structure, automated tests, and builds pass.

## Current requirement traceability

| ID | Current status | Current evidence | Genuine limitation, if any |
|---|---|---|---|
| R01 Unified sources | VERIFIED_WORKING | Customer, staff, camera and manual-admin sources share `Incident`; lifecycle tests and live transitions passed. | None in current core slice. |
| R02 Required stack | VERIFIED_WORKING | FastAPI/PostgreSQL/Alembic, React/Vite and Expo gates ran successfully; hybrid OpenCV/optional YOLO implementation is explicit. | External YOLO weights remain optional. |
| R03 Repository/developer setup | VERIFIED_WORKING | Separated backend/admin/mobile/docs tree, Docker setup, commands and five controlled videos exist. | None. |
| R04 Five roles | VERIFIED_WORKING | All five demo accounts passed login, refresh, `/auth/me`, logout; role-specific admin/mobile redirects exist. | None. |
| R05 Tenant and branch isolation | VERIFIED_WORKING | Live cross-branch and cross-organisation requests returned 404; security tests passed. | Broader future endpoints must retain the same policy. |
| R06 Customer navigation/report choices | VERIFIED_WORKING | 30 route files, central `report-options` route and report/suggestion choices; route and translation checks pass. | Device visual interaction was not observed. |
| R07 Home market/branch context | VERIFIED_WORKING | Live Nova/City switching changed market data, persisted selection, and preserved tenant owner. | Device visual interaction was not observed. |
| R08 Search/scanner/recent suggestions | PARTIALLY_WORKING | Debounced API search, scanner route, recent-search persistence and translated UI compile/lint. | Camera and touch interaction were not executed on a device. |
| R09 Dynamic home content | PARTIALLY_WORKING | Backend home/content data is market-scoped and live APIs passed; current mobile build succeeds. | Final visual card behaviour was not device-tested. |
| R10 Product customer flow | PARTIALLY_WORKING | Search/filter/sort/detail/price/favourite/barcode/report-prefill implementations compile; scoped product counts changed live. | Complete touch flow was not device-tested. |
| R11 Discount customer flow | PARTIALLY_WORKING | Campaign list/detail/categories/branches/dates/favourite exist; market-scoped campaign counts changed live. | Complete touch flow was not device-tested. |
| R12 Suggestions | PARTIALLY_WORKING | Backend persistence/status tests and mobile form/list/detail/timeline routes pass gates. | Customer-to-head-office visual story was not replayed in clients. |
| R13 Report wizard/upload | PARTIALLY_WORKING | API tests cover report/media; mobile has multi-step form, retry and byte-based XHR progress. | Full device upload workflow was not observed. |
| R14 Report tracking | PARTIALLY_WORKING | Live incident history and customer status mapping passed; detail/media/reasons compile. | Pull/visual timeline was not device-tested. |
| R15 Customer expiry OCR | PARTIALLY_WORKING | OCR candidate/confirmation implementation and backend tests pass. | Physical camera capture/OCR correction was not run. |
| R16 Loyalty | PARTIALLY_WORKING | Market-scoped cards changed live (Nova 2, City 1); cards/transactions/offers routes compile. | Loyalty UI and offer detail were not device-tested. |
| R17 Profile/settings/privacy | PARTIALLY_WORKING | Profile/preferences/language/notification/logout/delete APIs and screens are present and pass gates. | Full interactive device story was not run. |
| R18 Staff home | PARTIALLY_WORKING | STAFF role and audit metrics/routes are implemented; role auth and tests pass. | Staff dashboard was not visually exercised on device. |
| R19 Camera-assisted staff audit | PARTIALLY_WORKING | Barcode/OCR/confirmation/condition/completion backend integration tests pass and mobile builds. | Physical camera end-to-end was not observed. |
| R20 Audit quality controls | VERIFIED_WORKING | Automated tests cover duplicate attempts, quality flags and finding incidents; persistence is in DB models. | Hardware-dependent image quality remains environment-dependent. |
| R21 Re-audit | VERIFIED_WORKING | Assignment/comparison/mismatch persistence is covered by current tests. | None in tested API slice. |
| R22 Experimental smart audit | OUT_OF_SCOPE_BY_SPECIFICATION | No unsupported model claim is made. | Optional experimental feature is not implemented. |
| R23 Unified incident lifecycle | VERIFIED_WORKING | Current tests plus live assignment, rejection, manual resolution and reopen passed with immutable history. | None. |
| R24 Branch incident operations UI | PARTIALLY_WORKING | Proper modal/form components replaced browser prompts; every backing action passed live API verification and admin build. | Browser click-through unavailable. |
| R25 Camera rule configuration | VERIFIED_WORKING | Engine/ROI/threshold/persistence/state/FPS/error fields are exposed and tested. | Real RTSP deployment is not claimed. |
| R26 Camera event lifecycle | VERIFIED_WORKING | Controlled-video tests cover persistence, evidence, incident, clear period, auto-resolution and reopen/false-alert actions. | Controlled MP4, not RTSP. |
| R27 Honest hybrid vision | VERIFIED_WORKING | Hazard/promo/blocked rules are labelled OpenCV/ROI; optional YOLO is limited to applicable detection classes. | No custom hazard dataset/weights. |
| R28 Facial recognition | OUT_OF_SCOPE_BY_SPECIFICATION | Product and documentation explicitly exclude it. | Intentionally absent. |
| R29 Smart Store Score | VERIFIED_WORKING | Explainable score endpoint/ranking exists, respects tenant scope and is exercised by current tests/live requests. | MVP internal metric, not industry standard. |
| R30 Operational analytics | VERIFIED_WORKING | Live source/branch-filtered response matched DB exactly (`total 3`, `open 2`, seven metrics); date/status filters exist. | Visual chart interactions were not browser-tested. |
| R31 News management | PARTIALLY_WORKING | Platform/head content create/edit/delete actions passed live; customer news endpoints exist. | Full publish/archive UX semantics are not complete. |
| R32 Product/category management | PARTIALLY_WORKING | Product create/edit/delete passed live; categories/prices APIs and screens exist. | Bulk import and archive workflow remain incomplete. |
| R33 Branch-price management | PARTIALLY_WORKING | Branch price CRUD exists with role scoping. | Rich effective-date scheduling is incomplete. |
| R34 Campaign management | VERIFIED_WORKING | Campaign create/edit/delete passed live; dates, branches/products and customer market scope are implemented. | Browser form click-through unavailable. |
| R35 Branch management | PARTIALLY_WORKING | Platform branch creation and branch settings/routes exist. | Full coordinates/contact/configuration management is incomplete. |
| R36 Loyalty offers admin | PARTIALLY_WORKING | Customer offers and detail route exist and are market scoped. | Dedicated complete admin offer CRUD is incomplete. |
| R37 PostgreSQL schema/migrations | VERIFIED_WORKING | Fresh PostgreSQL upgrade to `0009`, current/check, full tests and seed counts passed after the migration repair. | Baseline's current-metadata pattern is legacy debt; guarded revisions now handle it. |
| R38 Authentication/account | VERIFIED_WORKING | Five-role live login/refresh/me/logout; automated tests cover auth/account behaviour. | Password email delivery is simulated UI, not an external integration. |
| R39 Organisations/branches/customer selection | VERIFIED_WORKING | Memberships=2, selection persisted, ownership unchanged, scoped branches/products/campaigns/cards changed. | None. |
| R40 Notifications | VERIFIED_WORKING | List/read/mark-all/preferences endpoints and translated mobile screens pass tests/gates. | External push provider is not integrated. |
| R41 Platform administration | PARTIALLY_WORKING | Cross-tenant organisation and admin activation/edit passed live; platform route set and build pass. | Browser UI and every secondary setting mutation were not exhaustively clicked. |
| R42 API hardening | PARTIALLY_WORKING | RBAC, validation, upload security and tenant tests pass. | Global rate limiting is not implemented. |
| R43 Media security | PARTIALLY_WORKING | Type/size/path upload-security tests pass and media metadata is scoped. | Fully signed/protected object-store delivery is not integrated. |
| R44 Retention/privacy enforcement | PARTIALLY_WORKING | Privacy/account-delete request UI/API exists. | Automated retention/deletion jobs are not implemented. |
| R45 Business rule documentation | PARTIALLY_WORKING | Architecture, product scope, vision and current audit docs exist. | Some non-core policy details remain product decisions. |
| R46 Design systems | PARTIALLY_WORKING | Reusable mobile/admin components, design tokens, builds and assets exist. | No direct browser/device visual QA in this run. |
| R47 Demo accounts | VERIFIED_WORKING | All five exact credentials completed current auth lifecycle. | None. |
| R48 Seed richness/idempotency | PARTIALLY_WORKING | Two runs kept counts at `2/4/30/6/2`; two markets and operational content are seeded. | Not every edge-case event/status is seeded. |
| R49 Core runtime stories | PARTIALLY_WORKING | API/DB stories, backend integration suite and controlled-video tests pass. | Client visual/hardware legs were not all replayed. |
| R50 Loading/empty/error states | PARTIALLY_WORKING | Reusable skeleton/empty/error/retry components exist and clients build. | Visual behaviour was not observed. |
| R51 Localisation | PARTIALLY_WORKING | Mobile integrity passed `237 AZ / 237 EN`; hard-coded customer strings have been substantially removed. | Admin still contains untranslated/hard-coded AZ/EN text. |
| R52 Offline/retry | PARTIALLY_WORKING | Upload retry, error and token refresh paths exist. | Offline/device network recovery was not runtime-tested. |
| R53 Logging/observability | PARTIALLY_WORKING | Health/log endpoints and processing-error fields exist. | Full structured centralized observability is not integrated. |
| R54 Acceptance/security | PARTIALLY_WORKING | Current backend suite, live role boundaries, scoped market data and builds pass. | A single browser/device end-to-end harness is absent. |
| R55 README/setup accuracy | VERIFIED_WORKING | README now records 0009, 36 tests, exact current gates and runtime results. | None. |
| R56 Environment configuration | PARTIALLY_WORKING | `.env.example`, Docker and documented DB/mobile API settings exist. | Some optional vision/OCR knobs remain runtime-specific. |
| R57 Code quality/modularity | PARTIALLY_WORKING | Admin feature/layout separation, ESLint and strict mobile TypeScript pass. | Backend static typing and some client service types can improve. |
| R58 Responsible AI wording | VERIFIED_WORKING | No 100% accuracy, theft, universal YOLO or MP4-as-RTSP claims; engine is shown per rule. | None. |
| R59 Visual reference fidelity | PARTIALLY_WORKING | Navy/blue/teal system and retail assets are implemented. | Screenshot-level comparison was unavailable. |
| R60 Customer screen inventory | PARTIALLY_WORKING | 30 Expo route files cover the connected core journeys. | Some originally enumerated screens are consolidated rather than separate routes. |
| R61 Staff screen inventory | PARTIALLY_WORKING | Dedicated staff/audit routes cover task, scan, OCR, review and completion states. | Several enumerated states are consolidated; device camera not observed. |
| R62 Admin route inventory | PARTIALLY_WORKING | Distinct `/branch`, `/head`, `/platform` layouts and route sets compile; RBAC is backend-enforced. | Visual route-by-route browser inspection unavailable. |
| R63 Accessibility | PARTIALLY_WORKING | Labels, focus styling, responsive CSS and 44px mobile target rules are implemented. | Formal keyboard/screen-reader/device audit was not run. |
| R64 Fictional retail assets | VERIFIED_WORKING | Product, campaign, news, branch and camera assets are organised in `backend/assets`; no emoji-dependent core UI. | Assets are fictional demo media by design. |
| R65 Typed API clients | PARTIALLY_WORKING | Shared service modules exist and strict mobile TypeScript passes. | Some admin/mobile API payloads still use `any`. |
| R66 Feature flags/modules | PARTIALLY_WORKING | Platform module activation is implemented. | Fine-grained customer/staff/vision rollout flags are incomplete. |
| R67 Deprecated UTC usage | VERIFIED_WORKING | Application code uses timezone-aware UTC helpers; no app-owned naive UTC warning appeared. | 105 warnings come from third-party `python-jose`. |
| R68 Android/iOS polish | PARTIALLY_WORKING | Expo Doctor, lint and strict TypeScript pass. | No physical Android/iOS layout run in this audit. |
| R69 Camera permissions | PARTIALLY_WORKING | Expo Camera permission/scanning/capture code exists and compiles. | Physical permission/camera behaviour was not exercised. |
| R70 Admin modal/form UX | PARTIALLY_WORKING | No browser `prompt()`/`confirm()` remains for audited flows; backing mutations passed live and build/lint pass. | Browser visual click-through unavailable. |
| R71 Final visual completion | PARTIALLY_WORKING | Current assets/design systems and build gates pass. | Pixel-level browser/device verification remains outstanding. |

## FINAL RE-AUDIT — 2026-07-29

### Exact database commands and results

The verification used a dedicated clean PostgreSQL database named `martiq_post0009_audit` on the running Docker PostgreSQL service; SQLite and mocked DBs were not used for migration/runtime evidence.

```powershell
docker compose up -d db
python -m alembic upgrade head
python -m alembic current
python -m alembic check
python -m scripts.seed
python -m scripts.seed
```

Observed successful rerun:

```text
0001 -> 0002 -> 0003 -> 0004 -> 0005 -> 0006 -> 0007 -> 0008 -> 0009
0009 (head)
No new upgrade operations detected.
Seeded 2 organisations, 4 branches and 30 products
counts after first seed: 2|4|30|6|2
Demo data already exists
counts after second seed: 2|4|30|6|2
```

The five count fields are organisations, branches, products, users and customer-market memberships.

### Exact quality-gate commands and results

```text
cd backend; python -m pytest -q
36 passed, 105 warnings in 15.55s

cd admin; npm run lint
eslint src --max-warnings 0
exit 0

cd admin; npm run build
vite v6.4.3 building for production...
1645 modules transformed
dist/assets/index-CIlVr_kz.js 290.96 kB (gzip 88.38 kB)
built in 3.33s

cd mobile; npm run lint
exit 0

cd mobile; npm run typecheck
tsc --noEmit
exit 0

cd mobile; npx expo-doctor
18/18 checks passed. No issues detected!

cd mobile; npm run check:i18n
Translation integrity passed: 237 AZ keys / 237 EN keys
```

### Role-by-role live results

FastAPI ran against the clean PostgreSQL audit database. Each role performed login, refresh-token exchange, `/auth/me`, and logout:

| Account | Reported role | Result |
|---|---|---|
| `customer@demo.az` | CUSTOMER | pass; refresh returned token, me matched, logout 204 |
| `staff@demo.az` | STAFF | pass; refresh returned token, me matched, logout 204 |
| `branch@demo.az` | BRANCH_ADMIN | pass; refresh returned token, me matched, logout 204 |
| `head@demo.az` | HEAD_OFFICE_ADMIN | pass; refresh returned token, me matched, logout 204 |
| `platform@martiq.az` | PLATFORM_ADMIN | pass; refresh returned token, me matched, logout 204 |

### Market context and isolation observations

```text
Nova Market: products=24, campaigns=1, cards=2, branches=3
CityMart: products=6, campaigns=1, cards=1, branches=1
owner_unchanged=True
selected_persisted=True
memberships=2
BRANCH_ADMIN cross-branch mutation: 404
HEAD_OFFICE_ADMIN cross-organisation request: 404
HEAD_OFFICE_ADMIN visible Nova branches: 3
```

Database inspection before and after market switching proved `User.organisation_id` did not change. `selected_organisation_id` changed and remained after a new `/auth/me` request. `CustomerMarketMembership` contained the two authorised markets. Home loyalty and the product, campaign, card and branch endpoints followed the selected market.

### Platform, content, modal-action and analytics observations

```text
PLATFORM_ADMIN cross-tenant organisation edit/activation: pass, state restored
PLATFORM_ADMIN administrator edit/activation: pass, state restored
product create/edit/delete: pass
news create/edit/delete: pass
campaign create/edit/delete: pass
incident assignment: pass
incident rejection: pass
incident manual resolution: pass
incident reopen: pass
analytics API total=3, direct DB total=3
analytics API open=2, direct DB open=2
analytics metric groups=7; branch/source/date/status filters present
```

The incident UI source uses modal forms, dropdowns, text areas and confirmations rather than browser prompts. The same backing transitions were executed live. Because no controllable browser was available (`agent.browsers.list()` returned an empty list), modal rendering and click behaviour are not labelled fully visually verified.

### Remaining genuine gaps

- Physical Android/iOS camera, barcode, image capture and OCR flows still require a device run.
- Browser-level visual inspection of every admin route and modal could not be performed in this environment.
- Admin AZ/EN localisation is incomplete even though mobile translation integrity is complete.
- Global API rate limiting, automated data-retention jobs and signed/object-store media delivery are not production-complete.
- Bulk product import/archive, rich price effective-date scheduling, full branch contact/coordinate configuration and complete loyalty-offer admin CRUD remain incomplete product-management depth.
- Some API payloads still use `any`; full backend static typing and a unified browser/device E2E harness remain engineering debt.
- Optional experimental smart audit, real RTSP deployment, external push/email providers, external loyalty systems and production custom vision models are approved later-phase integrations, not falsely claimed as complete.
