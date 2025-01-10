import os
from typing import Any, Dict, List
from nodetools.utilities.credentials import CredentialManager, get_credentials_directory
import boto3
import json
from xrpl.wallet import Wallet
from loguru import logger
from pydantic import BaseModel, Field

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV")


# NOTE: if you are running a reinstantiation of credentials, you must remove the "postfiatcreds" directory in your home dir
# Otherwise the encryption password must be the same as the one used previously


class NodeCredentials(BaseModel):
    """Validates the structure of node credentials"""

    xrpsecret: str = Field(description="XRP secret key")
    postgresconnstring: str = Field(description="PostgreSQL connection string")
    openrouter: str = Field(description="OpenRouter API key")
    openai: str = Field(description="OpenAI API key")
    discordbot_secret: str = Field(description="Discord bot secret")


class NodeConfig(BaseModel):
    """Validates the structure of node configuration"""

    node_name: str = Field(description="Name of the node")
    node_address: str = Field(default="", description="The address of the node")
    auto_handshake_addresses: List[str] = Field(description="address to autohandshake")
    discord_guild_id: int = Field(description="Discord guild ID")
    discord_activity_channel_id: int = Field(description="Discord activity channel ID")


class CredentialsConfig(BaseModel):
    """Root configuration model"""

    network: str = Field(
        default="testnet", description="the network to run on (testnet or mainnet)"
    )
    encryption_password: str = Field(
        min_length=8, description="Password for encrypting credentials"
    )
    credentials: NodeCredentials
    node_config: NodeConfig


class S3CredentialLoader:
    def __init__(self, bucket_name, credentials_path):
        """
        Initialize the S3 credential loader

        Args:
            bucket_name (str): Name of the S3 bucket
            credentials_path (str): Path to credentials file in S3
        """
        self.s3_client = boto3.client("s3")
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path

    def load_credentials_from_s3(self) -> CredentialsConfig:
        """
        Load credentials configuration from S3

        Returns:
            dict: Parsed credentials configuration
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=self.credentials_path
            )
            json_content = response["Body"].read().decode("utf-8")
            config_dict = json.loads(json_content)

            # Validate configuration using Pydantic
            return CredentialsConfig(**config_dict)

        except Exception as e:
            logger.error(f"Failed to load credentials from S3: {str(e)}")
            raise


def load_credentials_locally(path: str) -> CredentialsConfig:
    with open(path, "r") as json_file:
        config_dict = json.load(json_file)
        return CredentialsConfig(**config_dict)


def rename_creds(
    creds: NodeCredentials, network_suffix: str, prefix: str
) -> Dict[str, Any]:
    """
    Add rename creds to relevant credentials

    Args:
        network_suffix (str): the suffix appended onto discord bot secret
        prefix (str): The prefix appended onto some cred names

    Returns:
        dict: New dictionary with renamed credentials
    """
    cred_dict = creds.model_dump()
    renamed_creds = {}

    # Mapping of base credential names to renamed versions
    prefix_mapping = {
        "xrpsecret": f"{prefix}__v1xrpsecret",
        "postgresconnstring": f"{prefix}_postgresconnstring",
        "discordbot_secret": f"discordbot{network_suffix}_secret",
    }

    for base_name, value in cred_dict.items():
        if base_name in prefix_mapping:
            new_name = prefix_mapping[base_name]
            renamed_creds[new_name] = value
        else:
            renamed_creds[base_name] = value

    return renamed_creds


def configure_node(config: CredentialsConfig) -> str:
    """
    Set up node configuration using credentials from S3

    Args:
        config (CredentialsConfig): the config containing credentials and node configurations
    Returns:
        The encryption password
    """
    try:
        cm = CredentialManager(config.encryption_password)
        node_name = config.node_config.node_name

        network_suffix = "_testnet" if config.network == "testnet" else ""
        prefix = f"{node_name}{network_suffix}"
        # Rename certain credentials
        credentials_dict = rename_creds(config.credentials, network_suffix, prefix)

        # Set up wallet and node address
        node_wallet = Wallet.from_seed(credentials_dict[f"{prefix}__v1xrpsecret"])
        config.node_config.node_address = node_wallet.classic_address
        config.node_config.node_name = f"{node_name}{network_suffix}"

        # Save node configuration
        config_dir = get_credentials_directory()
        config_file = config_dir / f"pft_node_{config.network}_config.json"

        with open(config_file, "w") as file:
            json_content = config.node_config.model_dump_json(indent=2)
            file.write(json_content)

        # Store credentials
        cm.enter_and_encrypt_credential(credentials_dict)

        logger.info("Credential setup complete!")
        logger.info(f"Credentials stored in: {cm.db_path}")
        logger.info(f"Configuration stored in: {config_file}")

        return config.encryption_password
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        raise


def setup_node() -> str:
    """
    Sets up credentials in sqlite for the node to function correctly.
    Then returns the encryption password used to run the node.
    """
    try:
        if ENV != "local":
            BUCKET_NAME = os.getenv("BUCKET_NAME")
            CREDS_PATH = os.getenv("CREDENTIALS_PATH")

            if BUCKET_NAME is None or CREDS_PATH is None:
                raise Exception(
                    "Either bucket name or credentials path were not set in environment"
                )
            logger.info("Starting PostFiat Node Setup (S3 Configuration)")

            s3_loader = S3CredentialLoader(BUCKET_NAME, CREDS_PATH)

            # Load and validate configuration from S3
            config = s3_loader.load_credentials_from_s3()
        else:
            CRED_FILE_NAME = os.getenv("CREDENTIALS_FILE")
            if CRED_FILE_NAME is None:
                raise Exception(
                    "Credential file path is missing from environment when running with ENV=local"
                )
            logger.info("Starting PostFiat Node Setup (Local Configuration)")

            config = load_credentials_locally(CRED_FILE_NAME)

        return configure_node(config)
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        raise


if __name__ == "__main__":
    setup_node()
