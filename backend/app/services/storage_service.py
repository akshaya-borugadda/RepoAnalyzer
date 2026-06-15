from typing import Dict, Any

class StorageService:
    # Key: repo_name (string), Value: analysis result dictionary
    _analyses: Dict[str, Any] = {}
    
    @classmethod
    def save_analysis(cls, repo_name: str, data: Dict[str, Any]) -> None:
        """
        Stores the repository analysis results in memory.
        """
        cls._analyses[repo_name] = data
        
    @classmethod
    def get_analysis(cls, repo_name: str) -> Any:
        """
        Retrieves stored repository analysis results. Returns None if not found.
        """
        return cls._analyses.get(repo_name)
