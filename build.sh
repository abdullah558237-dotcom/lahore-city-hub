#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "=== 1/3 Installing Python Dependencies ==="
pip install -r requirements.txt

echo "=== 2/3 Compiling & Compressing Static Assets ==="
python manage.py collectstatic --noinput

echo "=== 3/3 Applying Database Migrations ==="
python manage.py migrate --noinput

echo "=== Build Completed Successfully ==="
