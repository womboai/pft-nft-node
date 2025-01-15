# Standard library imports
from typing import Dict, Any

# Third-party imports
from loguru import logger

from nodetools.models.models import (
    MemoConstructionParameters,
    MemoTransaction,
    ResponseGenerator,
)

# Task node imports
from nftnode.config import get_https_url
from nftnode.nft_processing.constants import TaskType

# NodeTools imports
from nodetools.configuration.configuration import (
    NetworkConfig,
    NodeConfig,
    RuntimeConfig,
)
from nodetools.protocols.generic_pft_utilities import GenericPFTUtilities
from nodetools.protocols.credentials import CredentialManager

from nftnode.nft_processing.nft_mint.nft import (
    MintError,
    NFTError,
    SellError,
    XRPLNFTMinter,
)
from nftnode.nft_processing.utils import derive_response_memo_type


class NFTMintResponseGenerator(ResponseGenerator):
    def __init__(
        self,
        node_config: NodeConfig,
        network_config: NetworkConfig,
        generic_pft_utilities: GenericPFTUtilities,
        credential_manager: CredentialManager,
    ):
        self._node_config = node_config
        self._generic_pft_utilities = generic_pft_utilities
        self._network_config = network_config
        self._credential_manager = credential_manager
        self._seed = self._credential_manager.get_credential(
            f"{self._node_config.node_name}__v1xrpsecret"
        )

    async def evaluate_request(self, request_tx: MemoTransaction) -> Dict[str, Any]:
        """Evaluate NFT mint request"""
        logger.info("Evaluating NFT mint request...")
        uri = request_tx.memo_data.strip()

        if uri == "":
            logger.debug("No memo_data was provided")
            return {"offer_id": None}

        try:
            https_url = get_https_url(self._network_config)
            minter = XRPLNFTMinter(https_url)

            logger.debug("Creating NFT and selling offer...")
            result = await minter.create_nft_for_recipient(
                issuer_seed=self._seed,
                recipient_address=request_tx.account,
                uri=uri,
                transfer_fee=0,
                amount="0",  # free offer
            )

            if isinstance(result, NFTError):
                logger.error(f"Failed to mint and transfer NFT: {result.message}")

                if isinstance(result.mint_result, MintError):
                    logger.error(
                        f"Failed to mint NFT with error: {result.mint_result.message}"
                    )
                if isinstance(result.offer_result, SellError):
                    logger.error(
                        f"Failed to make Sell Offer with error: {result.offer_result.message}"
                    )

                return {"offer_id": None}
            else:
                logger.info(
                    f"Successfully Minted NFT and made Sell offer with id: {result.offer_id}"
                )
                return {"offer_id": result.offer_id}

        except Exception as e:
            logger.error(f"Failed to mint NFT to receipient with error: {e}")
            return {"offer_id": None}

    async def construct_response(
        self, request_tx: MemoTransaction, evaluation_result: Dict[str, Any]
    ) -> MemoConstructionParameters:
        """Construct NFT response parameters"""

        logger.info("Constructing NFT response...")
        try:
            offer_id = evaluation_result["offer_id"]

            if offer_id is None:
                raise Exception("offer id from evaluating request was null")

            logger.debug(f"Constructing response with offer id: {offer_id}")
            response_string = "offer id: " + offer_id

            response_memo_type = derive_response_memo_type(
                request_memo_type=request_tx.memo_type,
                response_memo_type=TaskType.NFT_MINT_RESPONSE.value,
            )

            memo = MemoConstructionParameters.construct_standardized_memo(
                source=self._node_config.node_name,
                destination=request_tx.account,
                memo_data=response_string,
                memo_type=response_memo_type,
            )

            return memo
        except Exception as e:
            raise Exception(f"Failed to construct NFT response: {e}")
