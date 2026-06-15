# Repo Analyzer Backend (MVP Complete)

This project contains the backend service for **Repo Analyzer**, an application that accepts a GitHub repository URL, clones it, traverses its folder structure, and returns structural metrics, extension-based language counts, summaries, dead files tracking, API routing, and a Knowledge Graph representation. It also includes an interactive, rule-based codebase chatbot.

---

## Folder Structure & File Descriptions

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # Defines POST /analyze and POST /chat endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Stores path configurations (e.g. cloned_repos directory location)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── git_service.py      # Performs shallow git clone using GitPython to a unique temp directory
│   │   ├── analyzer_service.py # Core orchestrator that parses directories, stack details, and summaries
│   │   ├── stack_detector.py   # Scans configurations and dependencies for tech stacks, frameworks, and DBs
│   │   ├── summary_service.py  # Performs rule-based README parsing and important file explanations
│   │   ├── dead_file_service.py# Scans file references and handles import tracing to detect unused files
│   │   ├── api_detector.py     # Regex API route detector for Express, FastAPI, and Flask
│   │   ├── graph_service.py    # Builds a Knowledge Graph mapping files, directories, imports, and exports
│   │   ├── storage_service.py  # Simple in-memory cache to store analyses by repository name
│   │   └── chat_service.py     # Parses question triggers and extracts chatbot answers from analysis data
│   ├── utils/
│   │   ├── __init__.py
│   │   └── url_validator.py    # Matches URL against GitHub HTTPS/SSH patterns and parses owner/repo
│   ├── __init__.py
│   └── main.py                 # FastAPI application main entrypoint, initializes CORS and includes API routers
├── requirements.txt            # System dependencies (fastapi, uvicorn, gitpython, pydantic)
└── README.md                   # Installation and usage instructions (this file)
```

---

## Local Setup Instructions

### Prerequisites
1. **Python 3.8+** must be installed on your machine.
2. **Git** must be installed on your machine and available in your system path (GitPython wraps the system Git executable).
   - *Windows*: Download and run installer from [git-scm.com](https://git-scm.com/).
   - *macOS*: Run `brew install git`.
   - *Linux (Ubuntu/Debian)*: Run `sudo apt-get install git`.

### 1. Set Up a Virtual Environment
Navigate to the `backend/` directory in your terminal and run:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
Install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Run the API Server
Start the Uvicorn dev server:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
The server will start on `http://127.0.0.1:8000`. You can access the interactive API docs at `http://127.0.0.1:8000/docs`.

---

## How to Test in Swagger UI (`/docs`)

FastAPI generates automatic interactive documentation. To test the backend flow:

### Step 1: Run the Codebase Analysis
1. Open your browser and navigate to **`http://127.0.0.1:8000/docs`**.
2. Click on the **`POST /analyze`** dropdown.
3. Click the **"Try it out"** button in the top right of the section.
4. Modify the `repo_url` in the request body to point to a public GitHub repository. For example:
   ```json
   {
     "repo_url": "https://github.com/fastapi/fastapi"
   }
   ```
5. Click **"Execute"**.
6. Under the **Response body**, confirm you get a successful `200` JSON response containing the file tree, tech stack classification, important files purpose listing, detected API endpoints, dead files, and the `graph` node-edge representation.
7. **Important**: Note down the value of the `"repo_name"` field in the response (e.g. `"fastapi"` or the name of the repository you parsed). This is the key used to look up the analysis in memory.

### Step 2: Query the Repository Chatbot
1. Scroll down the Swagger UI and click on the **`POST /chat`** dropdown.
2. Click the **"Try it out"** button.
3. Complete the request body:
   - For `repo_name`, enter the exact `"repo_name"` from Step 1 (e.g. `"fastapi"`).
   - For `question`, write a query related to the repository.
   ```json
   {
     "repo_name": "fastapi",
     "question": "What is the tech stack?"
   }
   ```
4. Click **"Execute"**.
5. Inspect the **Response body** showing:
   - `answer`: Markdown text answering your question.
   - `sources`: Lists of source files referenced in building the answer.
6. Try asking different questions:
   - *"Explain the project."*
   - *"Which files are dead?"*
   - *"Show API routes."*
   - *"Which file connects to database?"* (if analyzing a DB-connected project)
   - *"Which file handles login?"*
