import os
from typing import Dict, Any, List, Tuple

# Mapping of file extensions to human-readable language names
EXTENSION_TO_LANGUAGE = {
    # Python
    '.py': 'Python',
    '.pyw': 'Python',
    # Web Technology
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    # JavaScript & TypeScript
    '.js': 'JavaScript',
    '.mjs': 'JavaScript',
    '.cjs': 'JavaScript',
    '.jsx': 'JavaScript (JSX)',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript (JSX)',
    # Data & Configuration
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.xml': 'XML',
    '.ini': 'INI Config',
    '.toml': 'TOML Config',
    # Shell Scripting
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.bat': 'Batch',
    '.ps1': 'PowerShell',
    # Main programming languages
    '.go': 'Go',
    '.rs': 'Rust',
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.kts': 'Kotlin',
    '.cpp': 'C++',
    '.hpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.c': 'C',
    '.h': 'C/C++ Header',
    '.cs': 'C#',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.sql': 'SQL',
    '.swift': 'Swift',
    '.dart': 'Dart',
    '.r': 'R',
    '.pl': 'Perl',
    '.pm': 'Perl',
    '.scala': 'Scala',
    '.tf': 'Terraform',
    # Markdown & Text
    '.md': 'Markdown',
    '.txt': 'Plain Text'
}

# Exact filename matches (for files without standard extensions)
FILENAME_TO_LANGUAGE = {
    'Dockerfile': 'Dockerfile',
    'dockerfile': 'Dockerfile',
    'Makefile': 'Makefile',
    'makefile': 'Makefile',
    'Jenkinsfile': 'Jenkins Pipeline',
    'LICENSE': 'License',
    'license': 'License'
}

class AnalyzerService:
    @staticmethod
    def analyze_repository(repo_path: str, repo_name: str) -> Dict[str, Any]:
        """
        Traverses a local directory, builds a structured folder/file tree,
        tallies totals, and computes language distributions.
        
        Args:
            repo_path (str): Absolute path to the cloned repository.
            repo_name (str): Name of the repository.
            
        Returns:
            Dict[str, Any]: Analysis summary including name, file/folder count,
                            language stats, and hierarchical directory tree.
        """
        # Directory names to skip during traversal
        ignore_set = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
        
        total_files = 0
        total_folders = 0
        languages_count: Dict[str, int] = {}
        
        def _get_language(file_path: str) -> str:
            filename = os.path.basename(file_path)
            # 1. Check direct name matches (e.g. Dockerfile)
            if filename in FILENAME_TO_LANGUAGE:
                return FILENAME_TO_LANGUAGE[filename]
            if filename.lower() in FILENAME_TO_LANGUAGE:
                return FILENAME_TO_LANGUAGE[filename.lower()]
                
            # 2. Check extension mappings
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext in EXTENSION_TO_LANGUAGE:
                return EXTENSION_TO_LANGUAGE[ext]
                
            # 3. Default fallback
            return ext.strip('.').upper() or 'Other'

        def _build_tree_recursive(current_dir: str, current_rel_path: str = "") -> List[Dict[str, Any]]:
            """
            Recursively scans a directory to construct a folder tree JSON.
            """
            nonlocal total_files, total_folders
            children = []
            
            try:
                # Get files and folders sorted alphabetically
                entries = sorted(os.listdir(current_dir))
            except PermissionError:
                # Gracefully return empty children list if access is denied
                return []
                
            for entry in entries:
                # Ignore directories/files specified in the ignore list (case-insensitive)
                if entry in ignore_set or entry.lower() in ignore_set:
                    continue
                    
                full_path = os.path.join(current_dir, entry)
                # Build POSIX-style relative path for frontend consistency
                rel_path = entry if not current_rel_path else f"{current_rel_path}/{entry}"
                
                if os.path.isdir(full_path):
                    total_folders += 1
                    sub_children = _build_tree_recursive(full_path, rel_path)
                    
                    children.append({
                        "name": entry,
                        "type": "dir",
                        "path": rel_path,
                        "children": sub_children
                    })
                else:
                    total_files += 1
                    lang = _get_language(full_path)
                    languages_count[lang] = languages_count.get(lang, 0) + 1
                    
                    children.append({
                        "name": entry,
                        "type": "file",
                        "path": rel_path
                    })
            
            # Sort directories first, then files alphabetically (case-insensitive)
            children.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
            return children

        # Perform recursive scanning
        tree = _build_tree_recursive(repo_path, "")
        
        # Sort language statistics by count (descending)
        sorted_languages = dict(
            sorted(languages_count.items(), key=lambda item: item[1], reverse=True)
        )
        
        # Run tech stack detection (Phase 2)
        from app.services.stack_detector import TechStackDetector
        stack_info = TechStackDetector.detect_stack(repo_path)
        
        # Run repository summarization & important file identification (Phase 3)
        from app.services.summary_service import SummaryService
        summary = SummaryService.generate_project_summary(repo_path, stack_info, sorted_languages)
        important_files = SummaryService.identify_important_files(repo_path)
        
        # Run dead file detection (Phase 4)
        from app.services.dead_file_service import DeadFileService
        dead_info = DeadFileService.detect_dead_files(repo_path)
        
        # Run API route detection (FEATURE 3)
        from app.services.api_detector import ApiDetector
        api_routes = ApiDetector.detect_routes(repo_path)
        
        # Run Knowledge Graph builder (FEATURE 1)
        from app.services.graph_service import GraphService
        graph = GraphService.build_graph(repo_path, repo_name, api_routes)
        
        # Run Architecture Flowchart generator (FEATURE 2)
        frontend = "Browser/Client"
        frameworks = stack_info["frameworks"]
        tech_stack = stack_info["tech_stack"]
        databases = stack_info["databases"]
        
        if "React" in frameworks:
            frontend = "React Frontend"
        elif "Next.js" in frameworks:
            frontend = "Next.js Frontend"
        elif "Vite" in frameworks:
            frontend = "Vite App"
            
        backend = "Backend Server"
        if "FastAPI" in frameworks:
            backend = "FastAPI Backend"
        elif "Flask" in frameworks:
            backend = "Flask Backend"
        elif "Django" in frameworks:
            backend = "Django Backend"
        elif "Express" in frameworks:
            backend = "Express Server"
        elif "Node.js" in tech_stack:
            backend = "Node.js Backend"
        elif "Python" in tech_stack:
            backend = "Python Script"
            
        flow_lines = ["graph TD"]
        flow_lines.append(f"    User([User/Client]) -->|Interacts| FE[\"{frontend}\"]")
        if backend != "Backend Server" or frontend == "Browser/Client":
            flow_lines.append(f"    FE -->|API Requests| BE[\"{backend}\"]")
        if databases:
            db_name = databases[0]
            flow_lines.append(f"    BE -->|Read/Write Data| DB[(\"{db_name} Database\")]")
        if "Docker" in tech_stack:
            flow_lines.append("    subgraph Containerization")
            flow_lines.append("        BE")
            if databases:
                flow_lines.append("        DB")
            flow_lines.append("    end")
            
        architecture_flowchart = "\n".join(flow_lines)
        
        # Run Health scoring & Insights extraction (Task 4 & Task 5)
        from app.services.health_service import HealthService
        health_info = HealthService.calculate_health_and_insights(
            repo_path=repo_path,
            stack_info=stack_info,
            languages=sorted_languages,
            api_routes=api_routes,
            important_files=important_files,
            dead_info=dead_info,
            total_files=total_files
        )
        
        # Assemble final result dictionary
        result = {
            "repo_name": repo_name,
            "total_files": total_files,
            "total_folders": total_folders,
            "languages": sorted_languages,
            "tree": tree,
            "project_type": stack_info["project_type"],
            "tech_stack": stack_info["tech_stack"],
            "frameworks": stack_info["frameworks"],
            "databases": stack_info["databases"],
            "confidence": stack_info["confidence"],
            "summary": summary,
            "important_files": important_files,
            "dead_files": dead_info["dead_files"],
            "dead_file_count": dead_info["dead_file_count"],
            "graph": graph,
            "architecture_flowchart": architecture_flowchart,
            "api_routes": api_routes,
            "health_score": health_info["health_score"],
            "health_report": health_info["health_report"],
            "insights": health_info["insights"]
        }
        
        # Save in memory (FEATURE 5)
        from app.services.storage_service import StorageService
        cached_result = result.copy()
        cached_result["repo_path"] = repo_path
        StorageService.save_analysis(repo_name, cached_result)
        
        return result
