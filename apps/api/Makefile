.PHONY: test sync run

test:
	pytest -q

sync:
	python -m scripts.run_sync --region US --period 7d

run:
	uvicorn app.main:app --reload
