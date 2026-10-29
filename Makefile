.PHONY: run test lint validate-maps

run:
	python -m uvicorn backend.app.api:app --reload

test:
	python -m pytest -q

lint:
	python -m ruff check .

validate-maps:
	python -m backend.app.validate_map backend/app/maps/himalayan_demo.json
	python -m backend.app.validate_map backend/app/maps/plains_demo.json
