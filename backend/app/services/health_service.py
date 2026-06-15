import os
from typing import Dict, Any, List

class HealthService:
    @staticmethod
    def calculate_health_and_insights(
        repo_path: str,
        stack_info: Dict[str, Any],
        languages: Dict[str, int],
        api_routes: List[Dict[str, Any]],
        important_files: List[Dict[str, Any]],
        dead_info: Dict[str, Any],
        total_files: int
    ) -> Dict[str, Any]:
        """
        Calculates repository health scores (0-100) and extracts development insights.
        
        Args:
            repo_path (str): Absolute path to the cloned repository.
            stack_info (dict): Detected tech stack details.
            languages (dict): Extension-based language statistics.
            api_routes (list): List of detected backend API endpoints.
            important_files (list): Catalog of important files.
            dead_info (dict): Results from the dead file scanner.
            total_files (int): Total number of files.
            
        Returns:
            Dict[str, Any]: Health score, breakdown report, and insights array.
        """
        # 1. DOCUMENTATION SCORE (0 - 100)
        doc_score = 100
        has_readme = False
        readme_size = 0
        
        for f in important_files:
            if f["file_path"].lower() == "readme.md":
                has_readme = True
                try:
                    p = os.path.join(repo_path, f["file_path"])
                    if os.path.exists(p):
                        readme_size = os.path.getsize(p)
                except Exception:
                    pass
                break
                
        if not has_readme:
            doc_score -= 30
        elif readme_size < 200:
            doc_score -= 15
        elif readme_size < 1000:
            doc_score -= 5
            
        doc_score = max(0, doc_score)
        
        # 2. STRUCTURE SCORE (0 - 100)
        struct_score = 100
        project_type = stack_info.get("project_type", "Unknown")
        if project_type == "Unknown":
            struct_score -= 20
            
        # Check for root file clutter
        root_files = 0
        try:
            for item in os.listdir(repo_path):
                if os.path.isfile(os.path.join(repo_path, item)) and not item.startswith('.'):
                    root_files += 1
        except Exception:
            pass
            
        if root_files > 15:
            struct_score -= 15
            
        # Check for standard directories (e.g. src, app, components, backend)
        standard_dirs = {'src', 'app', 'components', 'backend', 'frontend', 'lib', 'pages'}
        has_standard_dir = False
        try:
            for item in os.listdir(repo_path):
                if os.path.isdir(os.path.join(repo_path, item)) and item in standard_dirs:
                    has_standard_dir = True
                    break
        except Exception:
            pass
            
        if not has_standard_dir and total_files > 10:
            struct_score -= 15
            
        struct_score = max(0, struct_score)
        
        # 3. UNUSED CODE SCORE (0 - 100)
        unused_score = 100
        dead_count = dead_info.get("dead_file_count", 0)
        if total_files > 0:
            dead_ratio = dead_count / total_files
            if dead_ratio > 0:
                deduction = int(dead_ratio * 100 * 1.5)
                unused_score -= min(40, deduction)
                
        unused_score = max(0, unused_score)
        
        # 4. CONFIGURATION SCORE (0 - 100)
        config_score = 100
        has_dependency_config = False
        has_env_example = False
        has_docker_config = False
        
        tech_stack = stack_info.get("tech_stack", [])
        
        for f in important_files:
            fp_lower = f["file_path"].lower()
            if fp_lower in ("package.json", "requirements.txt", "pyproject.toml", "go.mod", "gemfile", "cargo.toml"):
                has_dependency_config = True
            if ".env.example" in fp_lower or "env.example" in fp_lower:
                has_env_example = True
            if "dockerfile" in fp_lower or "docker-compose" in fp_lower:
                has_docker_config = True
                
        if not has_dependency_config:
            config_score -= 20
            
        has_env_file = os.path.exists(os.path.join(repo_path, ".env"))
        if has_env_file and not has_env_example:
            config_score -= 15
            
        if "Docker" in tech_stack and not has_docker_config:
            config_score -= 10
            
        config_score = max(0, config_score)
        
        # 5. OVERALL HEALTH SCORE (Average of components)
        health_score = int((doc_score + struct_score + unused_score + config_score) / 4)
        
        # 6. EXTRACT CODEBASE INSIGHTS
        insights = []
        
        # Next.js App Router detection
        has_next_app_router = False
        for root, dirs, files in os.walk(repo_path):
            if "app" in dirs:
                app_path = os.path.join(root, "app")
                for _, _, sub_files in os.walk(app_path):
                    if any(f.endswith(('.tsx', '.ts', '.jsx', '.js')) and 'page' in f for f in sub_files):
                        has_next_app_router = True
                        break
            if has_next_app_router:
                break
                
        if has_next_app_router:
            insights.append("Uses Next.js App Router")
            
        # Supabase / Firebase check
        contains_supabase = False
        contains_firebase = False
        for f in important_files:
            fp_lower = f["file_path"].lower()
            if fp_lower in ("package.json", "requirements.txt"):
                try:
                    with open(os.path.join(repo_path, f["file_path"]), 'r', encoding='utf-8', errors='ignore') as f_obj:
                        pkg_content = f_obj.read().lower()
                        if "supabase" in pkg_content:
                            contains_supabase = True
                        if "firebase" in pkg_content:
                            contains_firebase = True
                except Exception:
                    pass
                    
        if contains_supabase:
            insights.append("Contains Supabase integration")
        if contains_firebase:
            insights.append("Contains Firebase integration")
            
        # Database migrations folders check
        migration_folders = ["migrations", "prisma/migrations", "alembic", "db/migrate"]
        has_migrations_folder = False
        for root, dirs, files in os.walk(repo_path):
            rel_root = os.path.relpath(root, repo_path).replace('\\', '/')
            if any(rel_root.startswith(mf) or rel_root == mf for mf in migration_folders):
                has_migrations_folder = True
                break
                
        databases = stack_info.get("databases", [])
        if databases:
            if not has_migrations_folder:
                insights.append("No database migrations found")
            else:
                insights.append("Contains database migration configs")
                
        # API layer scale
        if not api_routes:
            insights.append("No API routes detected")
        elif len(api_routes) <= 5:
            insights.append("API layer is minimal")
        else:
            insights.append("Features a robust API layer")
            
        # Docker config
        if has_docker_config or "Docker" in tech_stack:
            insights.append("Containerized with Docker")
            
        # Environment variables example check
        if has_env_file and not has_env_example:
            insights.append("Environment config example (.env.example) is missing")
            
        # Language dominance
        top_languages = list(languages.keys())[:2]
        if top_languages:
            insights.append(f"Mainly built with {', '.join(top_languages)}")
            
        # Fallback insight
        if not insights:
            insights.append("Clean project structure")
            
        return {
            "health_score": health_score,
            "health_report": {
                "structure": struct_score,
                "documentation": doc_score,
                "unused_code": unused_score,
                "configuration": config_score
            },
            "insights": insights
        }
