from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import NFTokenMint, NFTokenCreateOffer
from xrpl.utils import str_to_hex
from xrpl.asyncio.transaction import submit_and_wait
from typing import Optional


class XRPLNFTMinter:
    def __init__(self, api_url: str = "https://s.altnet.rippletest.net:51234"):
        """
        Initialize the NFT minting service.

        Args:
            api_url (str): URL of the XRPL node to connect to
        """
        self.client = AsyncJsonRpcClient(api_url)

    async def mint_nft(
        self,
        issuer_seed: str,
        uri: str,
        transfer_fee: int = 0,
        flags: int = 8,
        taxon: int = 0,
    ) -> dict:
        """
        Mint an NFT.

        Args:
            issuer_seed (str): The seed for the account minting the NFT
            uri (str): URI pointing to the NFT metadata
            transfer_fee (int): Fee percentage for secondary sales (0-50000 representing 0%-50%)
            flags (int): NFToken flags (8 for transferable tokens)
            taxon (int): Token taxon identifier

        Returns:
            dict: Transaction response with NFT ID and status
        """
        try:
            # Create wallet from seed
            wallet = Wallet.from_seed(seed=issuer_seed)

            # Convert URI to hex
            uri_hex = str_to_hex(uri)

            # Prepare NFTokenMint transaction
            mint_tx = NFTokenMint(
                account=wallet.classic_address,
                uri=uri_hex,
                flags=flags,
                transfer_fee=transfer_fee,
                nftoken_taxon=taxon,
            )

            # Submit and wait for validation
            response = await submit_and_wait(mint_tx, self.client, wallet)

            if response.result.get("meta", {}).get("TransactionResult") == "tesSUCCESS":
                # Extract NFTokenID from response
                nft_id = response.result["meta"].get("nftoken_id")

                return {
                    "status": "success",
                    "nft_id": nft_id,
                    "transaction_hash": response.result.get("hash"),
                    "validated": response.is_successful(),
                }
            else:
                return {
                    "status": "error",
                    "message": f"Transaction failed: {response.result.get('meta', {}).get('TransactionResult')}",
                    "transaction_hash": response.result.get("hash"),
                }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def create_sell_offer(
        self,
        owner_seed: str,
        nft_id: str,
        amount: str,
        destination: Optional[str] = None,
    ) -> dict:
        """
        Create a sell offer for an NFT.

        Args:
            owner_seed (str): Seed of the NFT owner's account
            nft_id (str): ID of the NFT to sell
            amount (str): Amount of XRP to sell for (e.g., "100")
            destination (str, optional): Specific buyer address

        Returns:
            dict: Transaction response
        """
        try:
            wallet = Wallet.from_seed(seed=owner_seed)

            # Create offer transaction
            offer_tx = NFTokenCreateOffer(
                account=wallet.classic_address,
                nftoken_id=nft_id,
                amount=amount,
                destination=destination,
                flags=1,  # Sellable
            )

            response = await submit_and_wait(
                offer_tx, wallet=wallet, client=self.client
            )

            if response.result.get("meta", {}).get("TransactionResult") == "tesSUCCESS":
                offer_id = response.result["meta"].get("offer_id")
                return {
                    "status": "success",
                    "offer_id": offer_id,
                    "transaction_hash": response.result.get("hash"),
                }
            else:
                return {
                    "status": "error",
                    "message": f"Offer creation failed: {response.result.get('meta', {}).get('TransactionResult')}",
                }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def create_nft_for_recipient(
        self,
        issuer_seed: str,
        recipient_address: str,
        uri: str,
        transfer_fee: int = 0,
        amount: str = "0",
    ) -> dict:
        """
        Create an NFT and transfer it to a recipient through a free sell offer.

        Args:
            issuer_seed (str): Seed of the minting account
            recipient_address (str): Classic address of the recipient
            uri (str): URI pointing to the NFT metadata
            transfer_fee (int): Fee percentage for secondary sales
            amount (str): Amount of XRP for the transfer (usually "0" for gifts)

        Returns:
            dict: Complete transaction response
        """
        # First mint the NFT
        mint_result = await self.mint_nft(issuer_seed, uri, transfer_fee)

        if mint_result["status"] != "success":
            return mint_result

        # Create a sell offer for the recipient
        offer_result = await self.create_sell_offer(
            owner_seed=issuer_seed,
            nft_id=mint_result["nft_id"],
            amount=amount,
            destination=recipient_address,
        )

        if offer_result["status"] != "success":
            return {
                "status": "error",
                "message": "Failed to create transfer offer",
                "mint_result": mint_result,
                "offer_result": offer_result,
            }

        return {
            "status": "success",
            "mint_result": mint_result,
            "offer_result": offer_result,
            "nft_id": mint_result["nft_id"],
            "offer_id": offer_result["offer_id"],
        }
