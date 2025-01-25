from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# load .env for nodetools
load_dotenv()


class Settings(BaseSettings):
    # default=... makes field required without explicitly needing to input it when calling Settings()
    env: Literal["local", "production", "development"] = Field(default=...)
    # whether to auto load creds or not (1 or 0)
    auto: Literal["1", "0"] = Field(default=...)
    encryption_password: str = Field(default=...)

    # api keys
    openrouter_api_key: str = Field(default=...)
    openai_api_key: str = Field(default=...)
    discord_bot_token: str = Field(default=...)

    # node
    network: Literal["testnet", "mainnet"] = Field(default=...)
    node_name: str = Field(default=...)
    pft_xrp_wallet: str = Field(default=...)
    rippled_rpc: str = Field(default=...)
    rippled_ws: str = Field(default=...)

    # database
    pg_conn_string: str = Field(default=...)

    # discord
    discord_guild_id: int = Field(default=...)
    discord_activity_channel_id: int = Field(default=...)

    class Config:
        env_file = ".env"


environ = Settings()
