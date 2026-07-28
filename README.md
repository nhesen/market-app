# MARTIQ

MARTIQ is a retail operations platform that combines camera incidents, employee audits, and customer reports in one workflow and manages each issue from detection to resolution.

## Working MVP slice

The repository contains a FastAPI API, Expo mobile client, React/Vite admin panel, PostgreSQL configuration, and a deterministic vision-event simulator. The first end-to-end slice is implemented: a customer submits a report, it creates a unified incident, a branch admin verifies and changes status, and the customer reads the same status timeline.

## Start locally

Prerequisites: Docker, Python 3.11+, Node 20+.

```bash
cp .env.example .env
docker compose up -d db
python -m pip install -r backend/requirements.txt
cd backend && python -m scripts.seed && uvicorn app.main:app --reload
cd admin && npm install && npm run dev
cd mobile && npm install && npx expo start
```

Admin: `http://localhost:5173`; API docs: `http://localhost:8000/docs`. For a physical phone set `EXPO_PUBLIC_API_URL` to the computer's LAN address.

Demo credentials (password `Demo123!`): `customer@demo.az`, `branch@demo.az`, `head@demo.az`, `staff@demo.az`, `platform@martiq.az`.

## Validation

```bash
cd backend && pytest
cd admin && npm run build
cd mobile && npm run typecheck
```

## Honest limitations

Price, loyalty, branch distance, and camera inputs are seeded demo data. The MP4 pipeline is a simulated continuous source and does not claim universal scene understanding. OCR is optional and dates require confirmation. Customer signals require branch verification. Smart Store Score is an explainable internal MVP metric, not an industry standard. No facial recognition or automatic accusation exists. See [product scope](docs/product-scope.md) and [architecture](docs/architecture.md).

