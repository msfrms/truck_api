from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # https://travistidwell.com/jsencrypt/demo/
    # https://www.base64encode.org/

    JWT_PUBLIC_KEY: str
    JWT_PRIVATE_KEY: str
    REFRESH_TOKEN_EXPIRES_IN: int
    ACCESS_TOKEN_EXPIRES_IN: int

    SENTRY_DSN: str

    DB_PASS: str
    DB_USER: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: str

    TELEGRAM_BOT_TOKEN: str
    CLIENT_ORIGIN: str

    CELERY_BROKER_URL: str

    class Config:
        env_file = "./.env"


settings = Settings()
