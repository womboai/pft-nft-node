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

from imagenode.task_processing.constants import IMAGE_GEN_COST
from imagenode.task_processing.image_gen.patterns import IMAGE_RESPONSE_PATTERN
from imagenode.task_processing.image_gen.response import ImageResponseGenerator
from imagenode.task_processing.utils import regex_to_sql_pattern


class ImageGenRule(RequestRule):
    """Pure business logic for queuing image generation tasks."""

    async def validate(self, tx: Dict[str, Any], dependencies: Dependencies) -> bool:
        """
        Validate business rules for a image generation request.
        Pattern matching is handled by TransactionGraph.
        Must:
        1. Be addressed to the node address
        2. Must have sent 1 PFT
        """
        if tx.get("destination") != dependencies.node_config.node_address:
            return False
        pft_amount = tx.get("pft_absolute_amount", 0)
        logger.debug(f"Received {pft_amount} PFT for an image generation request")
        if pft_amount < IMAGE_GEN_COST:
            return False

        return True

    async def find_response(
        self,
        request_tx: Dict[str, Any],
    ) -> Optional[ResponseQuery]:
        """Get query information for finding a image generation response."""
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

        # NOTE: look for image responses by the node
        params = {
            "account": request_tx["account"],
            "destination": request_tx["destination"],
            "request_time": request_tx["close_time_iso"],
            "response_memo_type": request_tx["memo_type"],
            "response_memo_data": regex_to_sql_pattern(
                IMAGE_RESPONSE_PATTERN.memo_data
            ),
        }

        return ResponseQuery(query=query, params=params)


class ImageGenResponseRule(ResponseRule):
    """Pure business logic for handling returning generated images"""

    async def validate(self, *args, **kwargs) -> bool:
        return True

    def get_response_generator(self, dependencies: Dependencies) -> ResponseGenerator:
        """Get response generator for images with dependencies"""
        return ImageResponseGenerator(
            node_config=dependencies.node_config,
            generic_pft_utilities=dependencies.generic_pft_utilities,
        )
