import os
import shutil
import uuid
import time
import git
from app.core.config import settings

class GitService:
    @staticmethod
    def clone_repository(repo_url: str, owner: str, repo_name: str) -> str:
        """
        Clones a public GitHub repository to a unique local path.
        
        Args:
            repo_url (str): The repository HTTPS/Git URL.
            owner (str): The owner of the repository.
            repo_name (str): The name of the repository.
            
        Returns:
            str: The absolute local directory path where the repository was cloned.
            
        Raises:
            ValueError: If the repository fails to clone.
        """
        # Ensure the parent cloned repositories folder exists
        os.makedirs(settings.CLONED_REPOS_DIR, exist_ok=True)
        
        # Generate a unique path name to prevent collisions during concurrency
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:6]
        folder_name = f"{owner}_{repo_name}_{timestamp}_{unique_id}"
        clone_path = os.path.join(settings.CLONED_REPOS_DIR, folder_name)
        
        try:
            # Perform a shallow clone (depth=1) to retrieve only the latest commit
            # This makes the cloning process extremely fast and lightweight.
            git.Repo.clone_from(repo_url, clone_path, depth=1)
            return clone_path
        except git.GitCommandError as e:
            # If cloning fails, clean up any partially created directory
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path, ignore_errors=True)
            raise ValueError(f"Git clone command failed. Ensure the URL is correct and public. Details: {e.stderr}")
        except Exception as e:
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path, ignore_errors=True)
            raise ValueError(f"An unexpected error occurred during cloning: {str(e)}")
