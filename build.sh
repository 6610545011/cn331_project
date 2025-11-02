#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser automatically if not exists
python manage.py createsuperuser \
  --username admin \
  --email "admin@email.com" \
  --noinput || true
