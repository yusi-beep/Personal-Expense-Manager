import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "devkey")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "expense.db")

class ProdConfig(Config):
    # Ако имаш DATABASE_URL (Postgres/MySQL/SQLite), ползвай него; иначе падни към локален sqlite
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "expense.db")
    )