# ---- Base (build/runtime) ----
FROM python:3.11-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies for reportlab/pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libfreetype6-dev \
      libjpeg62-turbo-dev \
      zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code
COPY . .

# Flask env
ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    APP_ENV=development

EXPOSE 5000

# By default, we launch the application
CMD ["flask", "run"]
