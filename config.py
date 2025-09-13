import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "devkey")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "expense.db")

class ProdConfig(Config):
     DEBUG = False
    # Ако имаш DATABASE_URL (Postgres/MySQL/SQLite), ползвай него; иначе падни към локален sqlite
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "expense.db")
    )
    
    # Production security enhancements
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    def __init__(self):
        super().__init__()
        # Ensure SECRET_KEY is not using the default in production
        if self.SECRET_KEY == "devkey":
            raise RuntimeError("SECRET_KEY must be set via environment variable for production deployment")