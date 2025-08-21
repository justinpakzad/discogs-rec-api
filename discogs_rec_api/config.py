from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_port: int = Field(alias="POSTGRES_PORT")
    postgres_host: str = Field(alias="POSTGRES_HOST")
    algortihm: str = Field(alias="ALGORITHM")
    secret_key: str = Field(alias="SECRET_KEY")
    model_config = SettingsConfigDict(case_sensitive=True)
    testing: bool = Field(alias="TESTING", default=False)

    @property
    def database_url(self):
        db = self.postgres_db if not self.testing else f"{self.postgres_db}_test"
        host = self.postgres_host if not self.testing else f"{self.postgres_host}_test"
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{host}:{self.postgres_port}/{db}"
        )

    @property
    def sync_database_url(self):
        db = self.postgres_db if not self.testing else f"{self.postgres_db}_test"
        host = self.postgres_host if not self.testing else f"{self.postgres_host}_test"
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{host}:{self.postgres_port}/{db}"
        )
