# Standard library imports
from typing import Dict, Any, Optional

# Third-party imports
from loguru import logger

# NodeTools imports
from nodetools.models.models import (
    ResponseQuery,
    RequestRule,
    ResponseRule,
    ResponseGenerator,
    Dependencies,
)

from nftnode.nft_processing.constants import NFT_MINT_COST
from nftnode.nft_processing.nft_mint.patterns import NFT_MINT_RESPONSE_PATTERN
from nftnode.nft_processing.nft_mint.response import NFTMintResponseGenerator
from nftnode.nft_processing.utils import regex_to_sql_pattern


class NFTMintRule(RequestRule):
    """Pure business logic for requesting NFT minting."""

    async def validate(self, tx: Dict[str, Any], dependencies: Dependencies) -> bool:
        """
        Validate business rules for a NFT mint request.
        Pattern matching is handled by TransactionGraph.
        Must:
        1. Be addressed to the node address
        2. Must have sent 1 PFT
        """
        if tx.get("destination") != dependencies.node_config.node_address:
            return False
        pft_amount = tx.get("pft_absolute_amount", 0)
        logger.debug(f"Received {pft_amount} PFT for an NFT mint request")
        if pft_amount < NFT_MINT_COST:
            return False

        return True

    async def find_response(
        self,
        request_tx: Dict[str, Any],
    ) -> Optional[ResponseQuery]:
        """Get query information for finding a NFT mint response."""
        query = """
            SELECT * FROM find_transaction_response(
                request_account := %(account)s,
                request_destination := %(destination)s,
                request_time := %(request_time)s,
                response_memo_type := %(response_memo_type)s,
                response_memo_data := %(response_memo_data)s,
                require_after_request := TRUE
            );
        """

        # NOTE: look for NFT mint responses by the node
        params = {
            "account": request_tx["account"],
            "destination": request_tx["destination"],
            "request_time": request_tx["close_time_iso"],
            "response_memo_type": request_tx["memo_type"],
            "response_memo_data": regex_to_sql_pattern(
                NFT_MINT_RESPONSE_PATTERN.memo_data
            ),
        }

        return ResponseQuery(query=query, params=params)


class NFTMintResponseRule(ResponseRule):
    """Pure business logic for handling returning minted NFT"""

    async def validate(self, *args, **kwargs) -> bool:
        return True

    def get_response_generator(self, dependencies: Dependencies) -> ResponseGenerator:
        """Get response generator for NFT minting with dependencies"""
        return NFTMintResponseGenerator(
            node_config=dependencies.node_config,
            generic_pft_utilities=dependencies.generic_pft_utilities,
            network_config=dependencies.network_config,
            credential_manager=dependencies.credential_manager,
        )
