import os
import logging


class Config:
    LOG_LEVEL = logging.DEBUG
    INTERVAL = 30  # seconds


class BaseFlaskConfig:
    ENV = "production"
    PORT = 8763
    HOST = "0.0.0.0"
    DEBUG = False
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(os.getcwd(), 'data.sqlite3')}"
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1024MB
