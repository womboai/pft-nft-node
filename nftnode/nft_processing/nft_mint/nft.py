from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models import Memo, NFTokenAcceptOffer
from xrpl.wallet import Wallet
from xrpl.models.transactions import NFTokenMint, NFTokenCreateOffer
from xrpl.utils import str_to_hex
from xrpl.asyncio.transaction import submit_and_wait
from typing import Optional
from dataclasses import dataclass


# Structs
@dataclass
class MintSuccess:
    nft_id: str
    transaction_hash: str | None
    validated: bool


@dataclass
class MintError:
    message: str
    transaction_hash: str | None


@dataclass
class SellSuccess:
    offer_id: str
    transaction_hash: str | None


@dataclass
class SellError:
    message: str


@dataclass
class NFTSuccess:
    mint_result: MintSuccess
    offer_result: SellSuccess
    nft_id: str
    offer_id: str


@dataclass
class NFTError:
    mint_result: MintError | MintSuccess
    message: str
    offer_result: SellError | None = None


@dataclass
class AcceptOfferSuccess:
    transaction_hash: str


@dataclass
class AcceptOfferError:
    message: str


# Implementation
class XRPLNFTMinter:
    _client: AsyncJsonRpcClient

    def __init__(self, api_url: str = "https://s.altnet.rippletest.net:51234"):
        """
        Initialize the NFT minting service.

        Args:
            api_url (str): URL of the XRPL node to connect to
        """
        self._client = AsyncJsonRpcClient(api_url)

    async def mint_nft(
        self,
        issuer_seed: str,
        uri: str,
        transfer_fee: int = 0,
        flags: int = 8,
        taxon: int = 0,
    ) -> MintSuccess | MintError:
        """
        Mint an NFT.

        Args:
            issuer_seed (str): The seed for the account minting the NFT
            uri (str): URI pointing to the NFT metadata
            transfer_fee (int): Fee percentage for secondary sales (0-50000 representing 0%-50%)
            flags (int): NFToken flags (8 for transferable tokens)
            taxon (int): Token taxon identifier

        Returns:
            MintSuccess | MintError: Successful or Error result from a NFTokenMint transaction attempt
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
            response = await submit_and_wait(mint_tx, self._client, wallet)

            if response.result.get("meta", {}).get("TransactionResult") == "tesSUCCESS":
                # Extract NFTokenID from response
                nft_id = response.result["meta"].get("nftoken_id")

                return MintSuccess(
                    nft_id=nft_id,
                    transaction_hash=response.result.get("hash"),
                    validated=response.is_successful(),
                )

            else:
                return MintError(
                    transaction_hash=response.result.get("hash"),
                    message=f"Transaction failed: {response.result.get('meta', {}).get('TransactionResult')}",
                )

        except Exception as e:
            return MintError(
                transaction_hash=None,
                message=str(e),
            )

    async def create_sell_offer(
        self,
        owner_seed: str,
        nft_id: str,
        amount: str,
        destination: Optional[str] = None,
    ) -> SellSuccess | SellError:
        """
        Create a sell offer for an NFT.

        Args:
            owner_seed (str): Seed of the NFT owner's account
            nft_id (str): ID of the NFT to sell
            amount (str): Amount of XRP to sell for (e.g., "100")
            destination (str, optional): Specific buyer address

        Returns:
            SellSuccess | SellError: Successful or Error result from the NFT sell offer.
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
                offer_tx, wallet=wallet, client=self._client
            )

            if response.result.get("meta", {}).get("TransactionResult") == "tesSUCCESS":
                offer_id = response.result["meta"].get("offer_id")
                return SellSuccess(
                    offer_id=offer_id, transaction_hash=response.result.get("hash")
                )
            else:
                return SellError(
                    message=f"Offer creation failed: {response.result.get('meta', {}).get('TransactionResult')}"
                )

        except Exception as e:
            return SellError(message=str(e))

    async def create_nft_for_recipient(
        self,
        issuer_seed: str,
        recipient_address: str,
        uri: str,
        transfer_fee: int = 0,
        amount: str = "0",
    ) -> NFTSuccess | NFTError:
        """
        Create an NFT and transfer it to a recipient through a free sell offer.

        Args:
            issuer_seed (str): Seed of the minting account
            recipient_address (str): Classic address of the recipient
            uri (str): URI pointing to the NFT metadata
            transfer_fee (int): Fee percentage for secondary sales
            amount (str): Amount of XRP for the transfer (usually "0" for gifts)

        Returns:
            NFTSuccess | NFTError: Either a successfuly or error NFT result
        """
        # First mint the NFT
        mint_result = await self.mint_nft(issuer_seed, uri, transfer_fee)

        if isinstance(mint_result, MintError):
            return NFTError(mint_result=mint_result, message="Failed to mint NFT")

        # Create a sell offer for the recipient
        offer_result = await self.create_sell_offer(
            owner_seed=issuer_seed,
            nft_id=mint_result.nft_id,
            amount=amount,
            destination=recipient_address,
        )

        if isinstance(offer_result, SellError):
            return NFTError(
                mint_result=mint_result,
                offer_result=offer_result,
                message="Failed to create transfer offer",
            )

        return NFTSuccess(
            mint_result=mint_result,
            offer_result=offer_result,
            nft_id=mint_result.nft_id,
            offer_id=offer_result.offer_id,
        )

    async def accept_offer(
        self, buyer_seed: str, offer_id: str
    ) -> AcceptOfferSuccess | AcceptOfferError:
        """
        Accept an NFT offer.

        Args:
            buyer_seed (str): Seed of the account accepting the offer
            offer_id (str): ID of the offer to accept

        Returns:
            AcceptOfferSuccess | AcceptOfferError: Success or Error result from attempting to accept
            an NFT offer.
        """
        try:
            wallet = Wallet.from_seed(seed=buyer_seed)

            # Accept offer transaction
            accept_tx = NFTokenAcceptOffer(
                account=wallet.classic_address,
                nftoken_sell_offer=offer_id,
            )

            response = await submit_and_wait(
                accept_tx, wallet=wallet, client=self._client
            )

            if response.result.get("meta", {}).get("TransactionResult") == "tesSUCCESS":
                tx_hash = response.result.get("hash")
                if tx_hash is None:
                    return AcceptOfferError(
                        message="Accept Offer tx successful, but hash could not be found."
                    )

                return AcceptOfferSuccess(transaction_hash=tx_hash)
            else:
                return AcceptOfferError(
                    message=f"Offer acceptance failed: {response.result.get('meta', {}).get('TransactionResult')}"
                )

        except Exception as e:
            return AcceptOfferError(message=str(e))
