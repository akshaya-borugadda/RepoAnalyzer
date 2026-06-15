from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings

# Initialize FastAPI app instance
app = FastAPI(
    title="Repo Analyzer API",
    description="API for cloning, traversing, and extracting metrics/file trees from public GitHub repositories.",
    version="1.0.0"
)

# Configure CORS middleware to enable external API integrations (e.g. React/Vite frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes under the root level (exposes POST /analyze)
app.include_router(api_router)

@app.get("/")
def root():
    """
    Root status endpoint displaying a welcome message and interactive docs link.
    """
    return {
        "message": "Welcome to the Repo Analyzer API (Phase 1).",
        "interactive_docs": "/docs"
    }
