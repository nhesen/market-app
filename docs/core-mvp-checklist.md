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
- [~] Products/search/barcode, news details, branches, favourites, profile
- [~] Suggestions, notifications, loyalty details and transactions
- [~] Login, registration and role redirect implemented; richer onboarding/market preference remains
- [x] Expo Camera barcode/date capture, media upload, OCR/manual confirmation and expired-result report handoff

## Staff
- [x] Role-specific navigation, audit lists, start/item/complete workflow
- [x] Duplicate prevention, quality flags, incident generation, re-audits and explainable score APIs

## Admin
- [x] Incident list/detail and status actions
- [~] Incident and suggestion operational views implemented; richer media case viewer remains
- [~] Product/news/price/campaign CRUD APIs and content inventory UI implemented; branch editor forms remain
- [ ] Audit management and quality review
- [ ] Head-office comparison and platform tenant management

## Vision, OCR and analytics
- [x] Deterministic persistence/clear-period simulator and auto-resolve test
- [~] OpenCV MP4 loop, cameras/ROIs/rules, hazard/promo scoring and telemetry implemented; production clips/queue approximation remain
- [x] OCR image upload/preprocessing/date extraction and explicit manual fallback
- [ ] Branch/head-office analytics and explainable score breakdown
