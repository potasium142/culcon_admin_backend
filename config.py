from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings):
    SECRET_KEY: str = ""
    TOKEN_EXPIRE_MINUTES: int = 30
    DB_URL: str = ""
    DB_URL_SUPA: str = ""
    MONGODB_URL: str = ""
    CLOUDINARY_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    model_config = SettingsConfigDict(env_file="dev.env")


env = Environment()
