from enum import Enum

NFT_MINT_COST = 1  # 1 PFT

# Super Users
DISCORD_SUPER_USER_IDS = [427471329365590017, 149706927868215297]


# Task types where the memo_type = task_id, requiring further disambiguation in the memo_data
class TaskType(Enum):
    """Task-related memo types for workflow management"""

    NFT_MINT = "NFT_MINT"
    NFT_MINT_RESPONSE = "NFT_MINT_RESPONSE"
