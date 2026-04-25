.PHONY: test sync run

test:
	python3 -m pytest -q

sync:
	python3 -m scripts.run_sync --region US --period 7d

run:
	python3 -m uvicorn app.main:app --reload
