# MARTIQ

MARTIQ is a retail operations platform that combines camera incidents, employee audits, and customer reports in one workflow and manages each issue from detection to resolution.

## Working MVP slice

The repository contains a FastAPI API, Expo mobile client, React/Vite admin panel, PostgreSQL configuration, and a deterministic vision-event simulator. The first end-to-end slice is implemented: a customer submits a report, it creates a unified incident, a branch admin verifies and changes status, and the customer reads the same status timeline.

## Verified local startup (PowerShell)

Prerequisites: Docker Desktop, Python 3.11+, and Node 20+. Start Docker Desktop first. The commands below use the real PostgreSQL service published on port 5432.

```powershell
Copy-Item .env.example .env
docker compose up -d db

cd backend
python -m pip install -r requirements.txt
$env:DATABASE_URL='postgresql+psycopg://martiq:martiq@localhost:5432/martiq'
python -m alembic upgrade head
python -m scripts.seed
python -m scripts.seed
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In separate PowerShell terminals:

```powershell
cd admin
npm install
npm run dev -- --host 0.0.0.0
```

```powershell
cd mobile
npm install --legacy-peer-deps
npx expo start
```

Admin: `http://localhost:5173`; API docs: `http://localhost:8000/docs`. For a physical phone set `EXPO_PUBLIC_API_URL` to the computer's LAN address.

Demo credentials (password `Demo123!`): `customer@demo.az`, `branch@demo.az`, `head@demo.az`, `staff@demo.az`, `platform@martiq.az`.

The React admin has independent route trees and navigation for `BRANCH_ADMIN` (`/branch`), `HEAD_OFFICE_ADMIN` (`/head`), and `PLATFORM_ADMIN` (`/platform`). These are presentation guards only; every corresponding API endpoint also enforces branch, organisation, or platform scope on the backend. Use `branch@demo.az`, `head@demo.az`, or `platform@martiq.az` to verify each workspace.

## Clean PostgreSQL verification

Warning: `docker compose down --volumes` deletes the local MARTIQ PostgreSQL volume. Use it only when a clean QA database is intended.

```powershell
docker compose down --volumes --remove-orphans
docker compose up -d db
cd backend
$env:DATABASE_URL='postgresql+psycopg://martiq:martiq@localhost:5432/martiq'
python -m alembic upgrade head
python -m alembic current
python -m scripts.seed
python -m scripts.seed
python -m alembic check
```

The 2026-07-31 customer-completion audit reached Alembic revision `0011 (head)` and `alembic check` printed `No new upgrade operations detected.` Revision 0010 adds persisted admin-audit operations and tenant-aware barcode uniqueness. Revision 0011 adds publishable bilingual news bodies and types, product package size, branch media/coordinates, and notification deep-link metadata. A newly-created PostgreSQL database migrated from zero through 0011 successfully.

The first seed printed `Seeded 2 organisations, 4 branches and 30 products`; the second printed `Demo data already exists`. Counts stayed `2 organisations / 4 branches / 30 products / 6 users / 2 memberships`, proving idempotency for the seeded rows. Customer market selection is stored separately from tenant ownership through `selected_organisation_id` and `customer_market_memberships`.

## Unified incident lifecycle

Customer reports, staff-audit findings, camera events, and manual admin entries now use one source-aware transition service. The internal lifecycle is `NEW`, `PRECHECK`, `VERIFICATION_REQUIRED`, `VERIFIED`, `ASSIGNED`, `IN_PROGRESS`, `RESOLUTION_CANDIDATE`, `AUTO_RESOLVED`, `MANUALLY_RESOLVED`, `REJECTED`, `REOPENED`, or `CANCELLED`. Invalid transitions return HTTP 409 with the current status and allowed destinations. Assignment, responsible department, SLA, resolution/rejection/reopening reasons, actor type, notes, attachments, and immutable transition history are returned by the admin API. Customer APIs expose only customer-visible notes and map internal states to `RECEIVED`, `CONFIRMED`, `IN_PROGRESS`, `RESOLVED`, `REJECTED`, or `CANCELLED`.

## Hybrid vision demo

Run `python -m scripts.generate_vision_videos` from `backend` to create reproducible normal, floor-hazard, blocked-aisle, depleted-promo and queue MP4 inputs. They are controlled pre-recorded demos, not RTSP. MARTIQ uses explicit OpenCV/ROI rules for the controlled hazard and coverage demos and reserves optional YOLO for applicable pretrained classes such as people. No labelled custom spill dataset or custom hazard weights are included, so the project does not describe its spill rule as YOLO. See [vision architecture](docs/vision.md).

## Staff camera audit

Sign in with `staff@demo.az` / `Demo123!`. STAFF sessions are routed to the dedicated audit panel. Open an assigned task, start it, scan each barcode with Expo Camera, capture the expiry-date field, review every OCR candidate, explicitly confirm or correct the date, choose the product condition, and review all saved items before completion. Confirmed expired, damaged, or invalid products create a `STAFF_AUDIT` incident visible to branch administration. Missing/unreadable images, invalid dates, duplicate scans, excessive OCR corrections, incomplete counts, short duration, and re-audit mismatches persist as audit quality flags.

## Quality gates

Run each block from the repository root in PowerShell:

```powershell
cd backend
python -m pytest -q
$env:DATABASE_URL='postgresql+psycopg://martiq:martiq@localhost:5432/martiq'
python -m alembic check
```

```powershell
cd admin
npm run lint
npm run build
```

```powershell
cd mobile
npm run lint
npm run typecheck
npx expo-doctor
```

The current 2026-07-29 results are:

- backend: `44 passed, 129 warnings in 28.71s`; warnings originate from `python-jose` using deprecated timezone-naive UTC internally;
- migration: `0011 (head)` and no Alembic drift;
- customer mobile: ESLint and strict TypeScript exited 0, translation integrity passed with `325 AZ / 325 EN` keys, Expo Doctor passed `18/18`, and Android export bundled `1,136` modules into a `3.39 MB` Hermes bundle;
- admin: ESLint exited 0; Vite 6.4.3 built 1,729 modules in 3.57s (`423.95 kB`, gzip `125.65 kB` JavaScript);
- mobile: ESLint exited 0; strict TypeScript exited 0; Expo Doctor passed `18/18` checks;
- translations: `237 AZ keys / 237 EN keys`;
- runtime auth: all five demo accounts passed login, refresh, `/auth/me`, and logout against the clean PostgreSQL database.

The same live run proved that switching between Nova Market and CityMart changes market-scoped product, campaign, card and branch results while leaving `User.organisation_id` unchanged. It also proved branch and organisation isolation with cross-scope requests returning 404, platform cross-tenant organisation/admin activation, content edit/delete, incident assignment/rejection/manual-resolution/reopen, and filtered operational analytics matching direct database counts. Full evidence and genuine remaining gaps are in [the compliance audit](docs/compliance-audit.md).

## Honest limitations

Price, loyalty, branch distance, and camera inputs are seeded demo data. The MP4 pipeline is a simulated continuous source and does not claim universal scene understanding. OCR is optional and dates require confirmation. Customer signals require branch verification. Smart Store Score is an explainable internal MVP metric, not an industry standard. No facial recognition or automatic accusation exists. See [product scope](docs/product-scope.md) and [architecture](docs/architecture.md).
