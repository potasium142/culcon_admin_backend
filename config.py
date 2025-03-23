from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings):
    SECRET_KEY: str = ""
    TOKEN_EXPIRE_MINUTES: int = 30000
    DB_URL: str = ""
    DB_URL_SUPA: str = ""
    DB_USERNAME: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "postgres"
    DB_PORT: int = 5432
    DB_DRIVER: str = "postgresql+psycopg"
    CLOUDINARY_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    LLM_ENDPOINT: str = ""
    LLM_USER_LIMIT: int = 7
    model_config = SettingsConfigDict(env_file="dev.env")


env = Environment()
