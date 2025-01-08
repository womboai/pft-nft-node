# Standard library imports
import os
from typing import Dict, Any

# Third-party imports
from loguru import logger

from nodetools.models.models import (
    ResponseGenerator,
    ResponseParameters,
)

# Task node imports
from tasknode.task_processing.constants import TaskType

# NodeTools imports
from nodetools.configuration.configuration import NodeConfig
from nodetools.protocols.generic_pft_utilities import GenericPFTUtilities

# Custom image generation imports
import fal_client

from tasknode.task_processing.ipfs import pin_by_url


class ImageResponseGenerator(ResponseGenerator):
    def __init__(
        self,
        node_config: NodeConfig,
        generic_pft_utilities: GenericPFTUtilities,
    ):
        self.node_config = node_config
        self.generic_pft_utilities = generic_pft_utilities

    async def evaluate_request(self, request_tx: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate image generation request"""
        logger.debug("Evaluating image generation request...")
        request_text = request_tx.get("memo_data")

        prompt = self._extract_prompt(request_text or "")

        if request_text is None or prompt is None:
            logger.debug("No memo_data was provided")
            return {"ipfs_hash": None}

        try:
            # Generate image
            result = await fal_client.subscribe_async(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                    "image_size": "square",
                    "num_images": 1,
                },
            )

            image_url = result["images"][0]["url"]

            # Pin image to IPFS
            data = pin_by_url(
                image_url,
                request_tx.get("hash") or "unknown_tx",
                os.getenv("PINATA_GROUP_ID"),
            )
            ipfs_hash = data["IpfsHash"]

            return {
                "ipfs_hash": ipfs_hash,
            }
        except Exception as e:
            logger.error(f"Failed to generate image with error: {e}")
            return {"ipfs_hash": None}

    def _extract_prompt(self, memo_data: str) -> str | None:
        prefix = "GENERATE IMAGE ___"
        if memo_data.startswith(prefix):
            return memo_data[len(prefix) :].strip()
        return None

    async def construct_response(
        self, request_tx: Dict[str, Any], evaluation_result: Dict[str, Any]
    ) -> ResponseParameters:
        """Construct image response parameters"""

        logger.debug("Constructing image generation response...")
        try:
            ipfs_hash = evaluation_result["ipfs_hash"]

            if ipfs_hash is None:
                raise Exception("ipfs hash from evaluating request was null")

            logger.debug(f"Constructing response with ipfs hash: {ipfs_hash}")

            response_string = (
                TaskType.IMAGE_GEN_RESPONSE.value + " ipfs hash: " + ipfs_hash
            )

            logger.debug(f"Constructed response string: {response_string}")

            memo = self.generic_pft_utilities.construct_memo(
                memo_data=response_string,
                memo_format=self.node_config.node_name,
                memo_type=request_tx["memo_type"],
            )

            return ResponseParameters(
                source=self.node_config.node_name,
                memo=memo,
                destination=request_tx["account"],
            )
        except Exception as e:
            raise Exception(f"Failed to construct image generation response: {e}")
