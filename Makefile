install:
	python -m pip install -r backend/requirements.txt
	cd admin && npm install
	cd mobile && npm install
api:
	cd backend && uvicorn app.main:app --reload
admin:
	cd admin && npm run dev
mobile:
	cd mobile && npx expo start
seed:
	cd backend && python -m scripts.seed
test:
	cd backend && pytest

