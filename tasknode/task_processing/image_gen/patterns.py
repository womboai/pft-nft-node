from nodetools.models.models import MemoPattern
import re
from tasknode.task_processing.constants import TaskType
from tasknode.task_processing.patterns import TASK_ID_PATTERN


IMAGE_GEN_PATTERN = MemoPattern(
    memo_type=TASK_ID_PATTERN,
    memo_data=re.compile(f".*{re.escape(TaskType.IMAGE_GEN.value)}.*"),
)

IMAGE_RESPONSE_PATTERN = MemoPattern(
    memo_type=TASK_ID_PATTERN,
    memo_data=re.compile(f".*{re.escape(TaskType.IMAGE_GEN_RESPONSE.value)}.*"),
)
