# Architecture

MARTIQ is a modular monolith. Expo and Vite clients call one versioned FastAPI REST API. SQLAlchemy owns persistence in PostgreSQL. Every tenant record is scoped by `organisation_id`; branch-admin access is additionally scoped by `branch_id`. Customer reports, audit findings, and camera events converge on `Incident` plus an append-only status history.

```text
Expo customer/staff ─┐
                     ├─ FastAPI ─ SQLAlchemy ─ PostgreSQL
React admin ─────────┘       ├─ local/S3-ready storage boundary
Vision simulator ────────────└─ unified incident service
```

The vision runner is hybrid and uses rule-specific persistence and clear thresholds. YOLO is limited to applicable pretrained objects such as people for queue counts; controlled hazard, promo-coverage and contour-support demos use explicit OpenCV/ROI rules. It can be disabled without affecting reports. Engine identity and evidence metadata are persisted with each event. See [vision architecture](vision.md). Storage, OCR, notifications, and vision sit behind replaceable service boundaries.
