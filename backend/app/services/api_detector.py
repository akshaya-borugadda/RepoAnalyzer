import os
import re
from typing import List, Dict, Any

class ApiDetector:
    # FastAPI route patterns (e.g., @app.get("/"), @router.post("/users"))
    FASTAPI_ROUTE_PATTERN = re.compile(
        r'@(?:app|router)\.(get|post|put|delete|patch|options|head)\(\s*[\'"]([^\'"]+)[\'"]',
        re.IGNORECASE
    )
    
    # Flask route patterns (e.g., @app.route("/api", methods=["POST"]))
    FLASK_ROUTE_PATTERN = re.compile(
        r'@app\.route\(\s*[\'"]([^\'"]+)[\'"](?:,\s*methods\s*=\s*\[([^\]]+)\])?',
        re.IGNORECASE
    )
    
    # Express route patterns (e.g., router.get("/users", ...), app.post("/login", ...))
    EXPRESS_ROUTE_PATTERN = re.compile(
        r'\b(?:app|router|express)\.(get|post|put|delete|patch|use)\(\s*[\'"]([^\'"]+)[\'"]',
        re.IGNORECASE
    )

    @staticmethod
    def detect_routes(repo_path: str) -> List[Dict[str, Any]]:
        """
        Traverses files in the cloned repository to detect and extract API routes.
        
        Args:
            repo_path (str): Absolute local path to the repository.
            
        Returns:
            List[Dict[str, Any]]: List of route descriptions containing method, path, and file_path.
        """
        api_routes = []
        ignore_folders = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
        
        for root, dirs, files in os.walk(repo_path):
            # Exclude ignored folders
            dirs[:] = [d for d in dirs if d not in ignore_folders and d.lower() not in ignore_folders]
            
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path).replace('\\', '/')
                
                path_lower = rel_path.lower().replace('\\', '/')
                _, ext = os.path.splitext(file.lower())
                
                # A. Detect Next.js App Router API Routes (e.g., app/api/users/route.ts)
                if ('app/api/' in path_lower or path_lower.startswith('api/')) and file.lower() in ('route.ts', 'route.js'):
                    try:
                        match = re.search(r'api/(.+)/route\.(?:ts|js)$', path_lower)
                        route_path = f"/api/{match.group(1)}" if match else "/api"
                        
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Search for exported handler functions (e.g., export async function GET)
                        methods_found = re.findall(
                            r'\bexport\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)\b', 
                            content
                        )
                        
                        # Default to GET if no export function methods were found
                        if not methods_found:
                            methods_found = ["GET"]
                            
                        for m in set(methods_found):
                            api_routes.append({
                                "method": m.upper(),
                                "path": route_path,
                                "file_path": rel_path
                            })
                    except Exception:
                        pass
                    continue  # Skip general line parsing for Next.js api route files
                
                # Skip files that aren't Python, Javascript, or Typescript
                if ext not in ('.py', '.js', '.jsx', '.ts', '.tsx'):
                    continue
                    
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    for line in lines:
                        line_stripped = line.strip()
                        
                        # Skip code comments
                        if line_stripped.startswith('#') or line_stripped.startswith('//'):
                            continue
                            
                        # B. Python (FastAPI/Flask) Route Parsing
                        if ext == '.py':
                            # 1. FastAPI Check
                            fastapi_match = ApiDetector.FASTAPI_ROUTE_PATTERN.search(line_stripped)
                            if fastapi_match:
                                method = fastapi_match.group(1).upper()
                                path = fastapi_match.group(2)
                                api_routes.append({
                                    "method": method,
                                    "path": path,
                                    "file_path": rel_path
                                })
                                continue
                                
                            # 2. Flask Check
                            flask_match = ApiDetector.FLASK_ROUTE_PATTERN.search(line_stripped)
                            if flask_match:
                                path = flask_match.group(1)
                                methods_group = flask_match.group(2)
                                if methods_group:
                                    methods = [
                                        m.strip().replace('\'', '').replace('"', '').upper() 
                                        for m in methods_group.split(',')
                                    ]
                                else:
                                    methods = ["GET"]
                                    
                                for method in methods:
                                    api_routes.append({
                                        "method": method,
                                        "path": path,
                                        "file_path": rel_path
                                    })
                                continue
                                
                        # C. JS/TS (Express) Route Parsing
                        elif ext in ('.js', '.ts', '.jsx', '.tsx'):
                            express_match = ApiDetector.EXPRESS_ROUTE_PATTERN.search(line_stripped)
                            if express_match:
                                method = express_match.group(1).upper()
                                path = express_match.group(2)
                                
                                # Skip general middleware mounting routes
                                if method == 'USE' and (not path.startswith('/') or path == '/*'):
                                    continue
                                    
                                if method == 'USE':
                                    method = 'ALL'
                                    
                                api_routes.append({
                                    "method": method,
                                    "path": path,
                                    "file_path": rel_path
                                })
                except Exception:
                    pass
                    
        return api_routes
