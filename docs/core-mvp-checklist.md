# Core MVP implementation checklist

Status legend: `[x]` verified, `[~]` implementation in progress, `[ ]` missing.

## Shared platform
- [x] FastAPI, SQLAlchemy, JWT access authentication, role checks
- [x] Organisation and branch isolation for current report/incident queries
- [~] Refresh tokens, logout, registration and account deletion implemented; server-side revocation remains production hardening
- [x] Alembic baseline plus retail migration tested
- [x] MIME/size-validated uploads and admin action log

## Customer
- [x] API-driven home, secure demo login, report creation and timeline
- [x] Products/search/barcode, news details, branches, favourites and profile flows
- [x] Suggestions, notifications, market-scoped loyalty details and transactions
- [x] Login, registration, verified session restore, onboarding and persistent market/branch preference
- [x] Universal customer market context is separated from tenant ownership through membership and selected-market fields
- [x] Expo Camera barcode/date capture, media upload, OCR/manual confirmation and expired-result report handoff

## Staff
- [x] Role-specific navigation, audit lists, start/item/complete workflow
- [x] Duplicate prevention, quality flags, incident generation, re-audits and explainable score APIs

## Admin
- [x] Incident list/detail and status actions
- [x] Incident/suggestion operational views, media viewer, lifecycle timeline and modal transition forms
- [x] Product/news/price/campaign CRUD APIs with modal edit and destructive confirmation UX
- [x] Audit management, quality flags and re-audit review
- [x] Head-office comparison plus platform tenant/admin create, edit and deactivate management

## Vision, OCR and analytics
- [x] Deterministic persistence/clear-period simulator and auto-resolve test
- [x] Controlled MP4 hybrid rules, cameras/ROIs, hazard/promo/blocked scoring, evidence and telemetry; optional YOLO queue requires real local weights and production ingestion remains out of scope
- [x] OCR image upload/preprocessing/date extraction and explicit manual fallback
- [x] Branch/head-office analytics, resolution/SLA/verification/re-audit breakdowns, filters and explainable score
