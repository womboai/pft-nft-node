from nodetools.configuration.configuration import NetworkConfig, RuntimeConfig


def get_https_url(network_config: NetworkConfig) -> str:
    https_url = (
        network_config.local_rpc_url
        if RuntimeConfig.HAS_LOCAL_NODE and network_config.local_rpc_url is not None
        else network_config.public_rpc_url
    )

    return https_url
