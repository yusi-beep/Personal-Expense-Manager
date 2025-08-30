# ---- Base (build/runtime) ----
FROM python:3.11-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системни зависимости за reportlab/pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libfreetype6-dev \
      libjpeg62-turbo-dev \
      zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код
COPY . .

# Flask env
ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    APP_ENV=development

EXPOSE 5000

# По подразбиране стартираме приложението
CMD ["flask", "run"]
