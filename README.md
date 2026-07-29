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

The current verified PostgreSQL run reached Alembic revision `0009 (head)`. The customer demo contains two switchable markets, four branches, 30 products, market-scoped campaigns/cards/offers, and idempotent enrichment; repeated seed runs print `Demo data already exists` without duplicating records. Customer market selection is stored separately from tenant ownership through `selected_organisation_id` and `customer_market_memberships`.

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

The last verified results were: backend `36 passed`; real PostgreSQL upgrades reached `0009 (head)`; Alembic reported `No new upgrade operations detected`; admin lint and production build passed; mobile lint and strict TypeScript passed.

## Honest limitations

Price, loyalty, branch distance, and camera inputs are seeded demo data. The MP4 pipeline is a simulated continuous source and does not claim universal scene understanding. OCR is optional and dates require confirmation. Customer signals require branch verification. Smart Store Score is an explainable internal MVP metric, not an industry standard. No facial recognition or automatic accusation exists. See [product scope](docs/product-scope.md) and [architecture](docs/architecture.md).
