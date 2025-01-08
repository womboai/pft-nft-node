##########################################################################
########################## HELPER FUNCTIONS ##############################
##########################################################################

import re
from tasknode.task_processing.patterns import TASK_ID_PATTERN

def is_valid_task_id(memo_type: str) -> bool:
    """Check if a memo type is a valid task ID"""
    return bool(TASK_ID_PATTERN.match(memo_type)) if memo_type else False

def regex_to_sql_pattern(pattern: re.Pattern) -> str:
    """Convert a regex pattern to SQL LIKE pattern"""
    pattern_str = pattern.pattern
    
    # First remove the optional whitespace pattern completely
    pattern_str = re.sub(r'\\s\?', '', pattern_str)
    
    # Then extract the core content between .* markers
    if match := re.match(r'\.\*(.*?)\.\*', pattern_str):
        clean_text = match.group(1).replace('\\', '')
        return f'%{clean_text}%'
    
    return f'%{pattern_str}%'

