FROM python:3.12
RUN apt-get update && apt-get install -y default-libmysqlclient-dev build-essential
RUN useradd -m -r appuser
WORKDIR /app
RUN mkdir -p /app/staticfiles
ENV PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
USER appuser
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]