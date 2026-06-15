from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.utils.url_validator import validate_github_url
from app.services.git_service import GitService
from app.services.analyzer_service import AnalyzerService

router = APIRouter()

class RepoAnalyzeRequest(BaseModel):
    repo_url: str = Field(
        ..., 
        description="The public GitHub repository URL (HTTPS or SSH) to clone and analyze.",
        examples=["https://github.com/fastapi/fastapi"]
    )

@router.post("/analyze", status_code=status.HTTP_200_OK)
def analyze_repository(payload: RepoAnalyzeRequest):
    """
    Accepts a public GitHub URL, validates it, clones the repository to local storage,
    traverses it, and returns the structural information (file tree, language distribution, counts).
    """
    repo_url = payload.repo_url
    
    # 1. Validate GitHub URL and parse owner/repo name
    is_valid, owner, repo_name = validate_github_url(repo_url)
    if not is_valid or not owner or not repo_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL. Please provide a standard public GitHub repository URL (e.g. 'https://github.com/owner/repo')."
        )
        
    # 2. Clone the repository using GitService
    try:
        cloned_path = GitService.clone_repository(repo_url, owner, repo_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    # 3. Analyze directory structure using AnalyzerService
    try:
        result = AnalyzerService.analyze_repository(cloned_path, repo_name)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze the repository contents: {str(e)}"
        )

class RepoChatRequest(BaseModel):
    question: str = Field(
        ..., 
        description="The question to ask about the repository.",
        examples=["Which file handles login?"]
    )
    repo_name: str = Field(
        ..., 
        description="The repository name (corresponding to a previously completed analysis).",
        examples=["fastapi"]
    )

@router.post("/chat", status_code=status.HTTP_200_OK)
def chat_repository(payload: RepoChatRequest):
    """
    Answers questions about the analyzed repository (e.g. tech stack, summary, routes, database, dead files)
    using rule-based metadata scans of the last saved analysis.
    """
    from app.services.chat_service import ChatService
    
    try:
        response = ChatService.answer_question(payload.repo_name, payload.question)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process the chat question: {str(e)}"
        )
