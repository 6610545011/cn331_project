#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

# อัปเกรด pip และติดตั้ง Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# รัน collectstatic
python manage.py collectstatic --no-input

# รัน migrations
python manage.py migrate

# -----------------------------------------------------------
# สร้าง Superuser โดยดึงรหัสผ่านจาก Environment Variable
# -----------------------------------------------------------

# ตรวจสอบว่ามี DJANGO_SUPERUSER_PASSWORD ใน Environment Variable หรือไม่
if [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Warning: DJANGO_SUPERUSER_PASSWORD not set. Skipping superuser creation."
else
    echo "Attempting to create superuser 'admin' using DJANGO_SUPERUSER_PASSWORD..."

    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'your@email.com', '$DJANGO_SUPERUSER_PASSWORD')" | python manage.py shell || true
    
    echo "Superuser creation command finished."
fi

# End of build.sh