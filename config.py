from os import environ as env
from dotenv import load_dotenv
load_dotenv()

class Config:
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = env.get("APP_SECRET_KEY")
    AUTH0_CLIENT_ID = env.get("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = env.get("AUTH0_CLIENT_SECRET")
    AUTH0_DOMAIN = env.get("AUTH0_DOMAIN")
    API_AUDIENCE = env.get("API_AUDIENCE")
    ALGORITHMS = env.get("ALGORITHMS")


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = env.get("DATABASE_URL")
    # to-do: add other production-specific configuration options

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = env.get("DATABASE_URL_TEST")
    TESTING = True
    # to-do: ther testing-specific configuration options
