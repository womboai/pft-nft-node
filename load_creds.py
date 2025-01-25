import json
from nftnode.settings import environ

import xrpl

from nodetools.utilities.credentials import CredentialManager, get_credentials_directory


def setup_node_auto():
    network = environ.network
    node_name = environ.node_name
    network_suffix = "_testnet" if network == "testnet" else ""
    encryption_password = environ.encryption_password
    credentials_dict = {
        f"{node_name}{network_suffix}_postgresconnstring": environ.pg_conn_string,
        f"{node_name}{network_suffix}__v1xrpsecret": environ.pft_xrp_wallet,
        "openrouter": environ.openrouter_api_key,
        "openai": environ.openai_api_key,
        f"discordbot{network_suffix}_secret": environ.discord_bot_token,
    }
    config = {
        "node_name": f"{node_name}{network_suffix}",
        "auto_handshake_addresses": [],
        "discord_guild_id": environ.discord_guild_id,
        "discord_activity_channel_id": environ.discord_activity_channel_id,
    }

    node_wallet = xrpl.wallet.Wallet.from_seed(
        credentials_dict[f"{node_name}{network_suffix}__v1xrpsecret"]
    )
    config["node_address"] = node_wallet.classic_address

    config_dir = get_credentials_directory()
    config_file = (
        config_dir
        / f"pft_node_{'testnet' if network == 'testnet' else 'mainnet'}_config.json"
    )
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    cm: CredentialManager = CredentialManager(encryption_password)
    cm.enter_and_encrypt_credential(credentials_dict)


if __name__ == "__main__":
    setup_node_auto()
