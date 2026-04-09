#!/bin/sh

echo "Waiting for MySQL..."
while ! python -c "import MySQLdb; MySQLdb.connect(host='db', user='$DATABASE_USER', passwd='$DATABASE_PASSWORD', db='$DATABASE_NAME')" 2>/dev/null; do
  echo "MySQL not ready, retrying..."
  sleep 2
done


echo "Running migrations..."
python manage.py migrate --noinput

if [ "$DJANGO_DEBUG" = "False" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

echo "Starting server..."
exec "$@"