# CVMatch API — Comandos útiles

.PHONY: start stop install freeze

start:
	source venv/bin/activate && uvicorn app.main:app --reload

stop:
	@echo "Presioná Ctrl+C para detener el servidor"

install:
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt

activate:
	@echo "Corré esto en tu terminal:"
	@echo "source venv/bin/activate"

venv:
	python3 -m venv venv
	source venv/bin/activate
	pip install -r requirements.txt