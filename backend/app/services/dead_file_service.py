import os
from typing import Dict, Any, List, Set, Tuple
from app.services.import_resolver import ImportResolver

class DeadFileService:
    @staticmethod
    def is_framework_entrypoint(rel_path: str) -> bool:
        """
        Determines if a file is a framework-specific entrypoint or layout component
        which should never be flagged as a dead file.
        """
        path_lower = rel_path.lower().replace('\\', '/')
        file_name = os.path.basename(path_lower)
        _, ext = os.path.splitext(file_name)
        
        # 1. FastAPI
        if file_name in ('main.py', 'app.py'):
            return True
            
        # 2. Express
        if file_name in ('server.js', 'app.js', 'index.js'):
            return True
            
        # 3. React
        if file_name in ('app.jsx', 'app.tsx', 'main.jsx', 'main.tsx'):
            return True
            
        # 4. Next.js App Router (app/page.tsx, app/layout.tsx, app/**/page.tsx, etc.)
        if 'app/' in path_lower or path_lower.startswith('app/'):
            if file_name in (
                'page.tsx', 'page.ts', 'page.jsx', 'page.js',
                'layout.tsx', 'layout.ts', 'layout.jsx', 'layout.js',
                'route.ts', 'route.js', 'loading.tsx', 'loading.ts',
                'error.tsx', 'error.ts', 'not-found.tsx', 'not-found.ts',
                'middleware.ts', 'middleware.js', 'global.css'
            ):
                return True
                
        # 5. Next.js Pages Router (pages/...)
        if 'pages/' in path_lower or path_lower.startswith('pages/'):
            if ext in ('.js', '.jsx', '.ts', '.tsx') and not file_name.startswith('_'):
                return True
                
        return False

    @staticmethod
    def detect_dead_files(repo_path: str) -> Dict[str, Any]:
        """
        Scans all files in the repository to identify orphaned modules not imported anywhere.
        """
        dead_files = []
        all_files: List[Tuple[str, str]] = []
        ignore_folders = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
        
        # 1. Walk directory to fetch all files
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ignore_folders and d.lower() not in ignore_folders]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path).replace('\\', '/')
                all_files.append((rel_path, full_path))
                
        # 2. Build dependency graph using ImportResolver
        dep_graph = ImportResolver.build_dependency_graph(repo_path)
        
        # Flatten all imported files to a set
        imported_files: Set[str] = set()
        for imports in dep_graph.values():
            for imp in imports:
                imported_files.add(imp)
                
        # 3. Ignored filenames, config files, and tests
        ignored_filenames = {
            'readme.md', 'package.json', 'requirements.txt', '.env', '__init__.py', 
            'package-lock.json', 'tsconfig.json', 'pnpm-lock.yaml', 'yarn.lock',
            'license', 'license.txt', 'docker-compose.yml', 'docker-compose.yaml', 'dockerfile',
            'next-env.d.ts', '.gitignore', '.eslintrc.json', '.prettierrc'
        }
        
        # 4. Check candidates
        for rel_path, full_path in all_files:
            file_name = os.path.basename(rel_path)
            file_lower = file_name.lower()
            _, ext = os.path.splitext(file_lower)
            
            # Skip non-source code files
            if ext not in ('.py', '.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.html'):
                continue
                
            # Skip ignored filenames
            if file_lower in ignored_filenames or file_name in ignored_filenames:
                continue
                
            # Skip tests
            if 'test' in file_lower or 'spec' in file_lower:
                continue
                
            # Skip configs
            if 'config' in file_lower or file_lower.endswith(('.toml', '.ini')):
                continue
                
            # Skip framework entrypoints
            if DeadFileService.is_framework_entrypoint(rel_path):
                continue
                
            # If it's not imported anywhere, it's flagged as dead
            if rel_path not in imported_files:
                confidence = "medium"
                
                # Context-aware reasoning
                if 'route' in file_name:
                    reason = "This route file is not registered or imported in any server configuration or router file."
                    confidence = "high"
                elif ext in ('.jsx', '.tsx') or 'component' in rel_path.lower():
                    reason = "This React component is not imported in App.jsx, main.jsx, or any other layout component."
                    confidence = "high"
                elif ext == '.py':
                    reason = "This Python module is not imported by any other Python files in the application."
                    confidence = "medium"
                else:
                    reason = "This file is not imported by any other source file."
                    confidence = "medium"
                    
                dead_files.append({
                    "file_path": rel_path,
                    "reason": reason,
                    "confidence": confidence
                })
                
        # Sort dead files alphabetically by path
        dead_files.sort(key=lambda x: x["file_path"].lower())
        
        return {
            "dead_files": dead_files,
            "dead_file_count": len(dead_files)
        }
