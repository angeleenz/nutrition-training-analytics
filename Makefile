.PHONY: install run migrate migrations superuser lint requirements clean help

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies using uv"
	@echo "  make run           - Run the development server"
	@echo "  make migrate       - Apply database migrations"
	@echo "  make migrations    - Create new migrations based on model changes"
	@echo "  make superuser     - Create a superuser"
	@echo "  make lint          - Run flake8 linting"
	@echo "  make requirements  - Export requirements.txt for deployment"
	@echo "  make clean         - Remove pycache and other temporary files"

install:
	uv sync

run:
	uv run python manage.py runserver

migrate:
	uv run python manage.py makemigrations
	uv run python manage.py migrate

migrations:
	uv run python manage.py makemigrations

superuser:
	uv run python manage.py createsuperuser

lint:
	uv run flake8

requirements:
	uv export --format requirements-txt > requirements.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
