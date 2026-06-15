import re
from typing import Tuple, Optional

# Regex matches https://github.com/owner/repo, http://github.com/owner/repo.git, git@github.com:owner/repo.git etc.
# Groups: 1 = owner, 2 = repository name
GITHUB_URL_PATTERN = re.compile(
    r'^(?:https?://github\.com/|git@github\.com:)([\w\-\.]+)/([\w\-\.]+?)(?:\.git)?/?$'
)

def validate_github_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates a GitHub repository URL and extracts owner and repository name.
    
    Args:
        url (str): The repository URL to validate.
        
    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (is_valid, owner, repo_name)
    """
    url = url.strip()
    match = GITHUB_URL_PATTERN.match(url)
    if not match:
        return False, None, None
    
    owner = match.group(1)
    repo_name = match.group(2)
    return True, owner, repo_name
