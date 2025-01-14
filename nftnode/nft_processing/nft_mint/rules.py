# Standard library imports
from typing import Optional

# NodeTools imports
from nodetools.models.models import (
    MemoTransaction,
    ResponseQuery,
    RequestRule,
    ResponseRule,
    ResponseGenerator,
    Dependencies,
    ValidationResult,
)

from nftnode.nft_processing.constants import NFT_MINT_COST, TaskType
from nftnode.nft_processing.nft_mint.response import NFTMintResponseGenerator
from nftnode.nft_processing.utils import derive_response_memo_type


class NFTMintRule(RequestRule):
    """Pure business logic for requesting NFT minting."""

    async def validate(
        self, tx: MemoTransaction, dependencies: Dependencies
    ) -> ValidationResult:
        """
        Validate business rules for a NFT mint request.
        Pattern matching is handled by TransactionGraph.
        Must:
        1. Be addressed to the node address
        2. Must have sent 1 PFT
        """
        if tx.get("destination") != dependencies.node_config.node_address:
            return ValidationResult(
                valid=False, notes=f"wrong destination address {tx.destination}"
            )
        if tx.pft_amount < NFT_MINT_COST:
            return ValidationResult(
                valid=False, notes=f"insufficient PFT amount: {tx.pft_amount}"
            )

        return ValidationResult(valid=True)

    async def find_response(
        self,
        request_tx: MemoTransaction,
    ) -> Optional[ResponseQuery]:
        """Get query information for finding a NFT mint response."""
        query = """
            SELECT * FROM find_transaction_response(
                request_account := %(account)s,
                request_destination := %(destination)s,
                request_time := %(request_time)s,
                response_memo_type := %(response_memo_type)s,
                require_after_request := TRUE
            );
        """

        response_memo_type = derive_response_memo_type(
            request_memo_type=request_tx.memo_type,
            response_memo_type=TaskType.NFT_MINT_RESPONSE.value,
        )
        # NOTE: look for nft responses by the node that match the given request
        params = {
            "account": request_tx.account,
            "destination": request_tx.destination,
            "request_time": request_tx.datetime,
            "response_memo_type": response_memo_type,
        }

        return ResponseQuery(query=query, params=params)


class NFTMintResponseRule(ResponseRule):
    """Pure business logic for handling returning minted NFT"""

    async def validate(
        self, tx: MemoTransaction, dependencies: Dependencies
    ) -> ValidationResult:
        return ValidationResult(valid=True)

    def get_response_generator(self, dependencies: Dependencies) -> ResponseGenerator:
        """Get response generator for NFT minting with dependencies"""
        return NFTMintResponseGenerator(
            node_config=dependencies.node_config,
            generic_pft_utilities=dependencies.generic_pft_utilities,
            network_config=dependencies.network_config,
            credential_manager=dependencies.credential_manager,
        )
