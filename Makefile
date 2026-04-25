# ── API ──────────────────────────────────────────
api-install:
	pip install -r apps/api/requirements.txt

api-run:
	cd apps/api && uvicorn app.main:app --reload

api-test:
	cd apps/api && pytest -q

api-sync:
	cd apps/api && python -m scripts.run_sync --region US --period 7d

# ── Dashboard ───────────────────────────────────
dash-install:
	cd apps/dashboard && npm install

dash-dev:
	cd apps/dashboard && npm run dev

dash-build:
	cd apps/dashboard && npm run build

# ── All ─────────────────────────────────────────
install: api-install dash-install

dev:
	$(MAKE) api-run & $(MAKE) dash-dev
