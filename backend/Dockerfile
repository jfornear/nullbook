FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

RUN useradd -m -r nullbook && chown -R nullbook:nullbook /app
USER nullbook

EXPOSE 8001

CMD ["gunicorn", "nullbook.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "3", "--timeout", "300"]
