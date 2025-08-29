# Dev-friendly образ за локално тестване със SQLite
FROM python:3.11-slim

WORKDIR /app

# Системни зависимости за reportlab, pillow и пр. (минимални)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libfreetype6-dev libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Инсталирай Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирай приложението
COPY . .

# Env за Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
# Използваме dev конфиг; може да override-неш с --env-file .env
ENV APP_ENV=development

# Порт
EXPOSE 5000

# Стартирай
CMD ["flask", "run"]

#Вариант A: Без Docker (най-лесно)----------------
# 1) създай и активирай venv (по желание)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# 2) зависимости
pip install -r requirements.txt

# 3) .env вече е в корена → app.py ще го прочете
# (ако искаш, можеш да export-неш само APP_ENV=development)

# 4) старт
python app.py
# отвори http://127.0.0.1:5000/

#Вариант B: С Docker (SQLite)-------------
# билд
docker build -t expense-tracker .

# пусни контейнер с порт mapping и .env
# добавяме volume за expense.db, за да ПЕРСИСТИРА между рестарти
docker run --rm -p 5000:5000 --env-file .env \
  -v "$(pwd)/expense.db:/app/expense.db" \
  expense-tracker

# отвори http://localhost:5000/

    #--------------------------------------
    #Ако си на Windows PowerShell, използвай:
    docker run --rm -p 5000:5000 --env-file .env `
      -v ${PWD}\expense.db:/app/expense.db `
      expense-tracker


