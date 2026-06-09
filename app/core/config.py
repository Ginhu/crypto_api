from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CryptoAPI"
    debug: bool = False
    mongo_uri: str = "mongodb://localhost:27017"

    class Config:
        env_file = ".env"


settings = Settings()
