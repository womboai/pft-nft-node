from nodetools.models.models import MemoPattern
import re
from nftnode.nft_processing.constants import TaskType
from nodetools.configuration.constants import UNIQUE_ID_PATTERN_V1


NFT_MINT_PATTERN = MemoPattern(
    memo_type=re.compile(
        f"^{UNIQUE_ID_PATTERN_V1.pattern}__{TaskType.NFT_MINT.value}$"
    ),
)

NFT_MINT_RESPONSE_PATTERN = MemoPattern(
    memo_type=re.compile(
        f"^{UNIQUE_ID_PATTERN_V1.pattern}__{TaskType.NFT_MINT_RESPONSE.value}$"
    ),
)
