from nodetools.models.models import MemoPattern
import re
from nftnode.nft_processing.constants import TaskType
from nftnode.nft_processing.patterns import TASK_ID_PATTERN


NFT_MINT_PATTERN = MemoPattern(
    memo_type=TASK_ID_PATTERN,
    memo_data=re.compile(f".*{re.escape(TaskType.NFT_MINT.value)}.*"),
)

NFT_MINT_RESPONSE_PATTERN = MemoPattern(
    memo_type=TASK_ID_PATTERN,
    memo_data=re.compile(f".*{re.escape(TaskType.NFT_MINT_RESPONSE.value)}.*"),
)
