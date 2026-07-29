# MARTIQ comprehensive QA report

Date: 2026-07-29  
Scope: backend API/database, tenant and role security, media, audit/re-audit, OCR, OpenCV vision, migrations, mobile Expo project, admin production build, dependencies and route inventory.

## Executive result

The implemented MVP slices pass automated functional, type and build validation. QA expanded backend coverage from 12 to 16 tests and found/fixed missing Expo native peers, an SDK patch mismatch, dead mobile navigation targets, demo-only authentication behavior, report media linkage, and missing cross-tenant/re-audit/real-MP4 coverage.

## Commands and results

| Area | Command | Result |
|---|---|---|
| Backend | `python -m pytest -q` | **36 passed** |
| Python syntax/imports | `python -m compileall -q app scripts` | **Passed** |
| Migrations | `python -m alembic upgrade head` on Docker PostgreSQL | **0001–0009 passed; no drift** |
| Seed | `python -m scripts.seed` twice | **2 switchable markets, 4 branches, 30 products; second run idempotent** |
| Mobile types | `npm run typecheck` | **Passed** |
| Expo compatibility | `npx expo-doctor` | **18/18 checks passed** |
| Admin | `npm run build` | **Passed** |

## Backend functional matrix

- Authentication: customer/branch/staff/head-office/platform login, refresh and registration covered.
- Role security: customer admin denial and tenant-admin platform denial covered.
- Tenant isolation: CityMart branch admin cannot list or update Nova Market incidents.
- Branch isolation: Nərimanov branch admin cannot list a Yasamal-only incident.
- Customer content: product search, favourites, news CRUD reflection and suggestion tracking covered.
- Reports: customer create → incident → admin status → customer timeline covered.
- Media: MIME rejection, accepted image asset, asset ownership and incident attachment linkage covered.
- Staff audit: start, duplicate prevention, item submission, completion and finding-created incident covered.
- Re-audit: different employee assignment, mismatch comparison and quality-flag creation covered.
- OCR: supported date formats, multiple candidates and empty/unreadable fallback covered.
- Vision rule engine: persistence and clear-period auto-resolution covered.
- Real MP4 path: a generated seven-frame MP4 is decoded with OpenCV, opens an event after persistence and auto-resolves after clear frames.
- Analytics: explainable branch-score bounds and breakdown covered.
- Content administration: head-office product/news creation and immediate customer visibility covered.

## Defects fixed during QA

1. Missing Expo Router native peers (`expo-constants`, `expo-linking`, `react-native-safe-area-context`, `react-native-screens`).
2. React Native `0.76.5` did not match Expo SDK 52 expected patch; upgraded through `expo install` to `0.76.9`.
3. Home quick actions and Prices/Cards/Profile navigation were not connected.
4. Mobile home silently forced the demo customer after any error; it now routes to login.
5. Mobile login/register, verified session restore and staff role routing are present and revalidated.
6. Report uploads existed but were not linked to incidents; `IncidentAttachment` and ownership checks were added.
7. Re-audit consistency, employee quality-score and head-office operational analytics paths are present and tested.
8. Tests did not prove cross-tenant/cross-branch isolation or real MP4 decoding; both are now covered.

## Dependency security review

### Admin

`react-router-dom` is pinned to `7.18.1`. npm reports a high advisory for React Router RSC action processing. MARTIQ admin uses classic client-side `BrowserRouter` only—no RSC, server actions, SSR, `ScrollRestoration`, or framework action endpoints—so the reported vulnerable path is not reachable in this application. The package must still be upgraded when the React Router project publishes a release that resolves the RSC advisory without reintroducing the broader redirect/XSS advisories affecting older versions.

### Mobile

Expo SDK 52's CLI/build dependency tree reports transitive advisories in `tar`, `glob`, `postcss`, `xmldom`, and related build tooling. The application does not parse attacker-supplied tar/XML/CSS through these CLI paths at runtime. `npm audit fix --force` proposes Expo 57, which is a major SDK jump and was intentionally not applied blindly. Safe plan: create a dedicated Expo SDK upgrade branch, follow sequential Expo upgrade guidance, regenerate native projects, rerun `expo-doctor`, device camera tests and EAS builds.

## Known QA constraints

- The in-app browser backend was unavailable in this session (`agent.browsers.list()` returned empty), so visual click-through and screenshot comparison could not be executed. Source routes, admin production compilation and mobile type validation passed.
- Physical-device camera, notification permission and barcode performance require iOS/Android hardware testing.
- EasyOCR is optional. Without it, the API explicitly returns `manual-fallback`; it never claims OCR success.
- Real RTSP/NVR, loyalty, POS/ERP, S3 and push-provider behavior require external systems and credentials.
- Python 3.13 emits `datetime.utcnow()` deprecation warnings. They do not fail tests, but timestamps should migrate to a consistent timezone-aware UTC helper before production rollout.

## Recommended release gate

Before a pilot build: complete one Android and one iOS physical-device run covering camera permission denial/acceptance, EAN-13 scan, image/video upload and report tracking; complete a desktop browser walkthrough for every admin route; and perform future Expo SDK upgrades in an isolated branch. Docker PostgreSQL runtime verification is complete.
