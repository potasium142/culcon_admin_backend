from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings):
    SECRET_KEY: str = ""
    TOKEN_EXPIRE_MINUTES: int = 30
    DB_URL: str = ""

    model_config = SettingsConfigDict(env_file="dev.env")


env = Environment()
