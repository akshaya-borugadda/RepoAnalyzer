import os
import json
import re
from typing import Dict, Any, List, Set

class TechStackDetector:
    @staticmethod
    def detect_stack(repo_path: str) -> Dict[str, Any]:
        """
        Scans a repository to identify the programming languages, frameworks,
        databases, and development tools used, returning confidence scores.
        
        Args:
            repo_path (str): Absolute local path to the cloned repository.
            
        Returns:
            Dict[str, Any]: Tech stack metadata including project_type, tech_stack,
                            frameworks, databases, and a confidence map.
        """
        tech_stack: Set[str] = set()
        frameworks: Set[str] = set()
        databases: Set[str] = set()
        confidence: Dict[str, str] = {}
        
        project_types: Set[str] = set()
        
        # File paths to scan
        package_json_path = os.path.join(repo_path, 'package.json')
        requirements_path = os.path.join(repo_path, 'requirements.txt')
        dockerfile_path = os.path.join(repo_path, 'Dockerfile')
        docker_compose_yml = os.path.join(repo_path, 'docker-compose.yml')
        docker_compose_yaml = os.path.join(repo_path, 'docker-compose.yaml')
        env_path = os.path.join(repo_path, '.env')
        
        # 1. Node.js & Javascript/TypeScript Frameworks
        if os.path.exists(package_json_path):
            tech_stack.add("Node.js")
            project_types.add("Node.js")
            confidence["Node.js"] = "High"
            
            try:
                with open(package_json_path, 'r', encoding='utf-8', errors='ignore') as f:
                    pkg_data = json.load(f)
                
                # Combine dependencies, devDependencies, peerDependencies
                deps: Dict[str, str] = {}
                if isinstance(pkg_data, dict):
                    deps.update(pkg_data.get("dependencies", {}))
                    deps.update(pkg_data.get("devDependencies", {}))
                    deps.update(pkg_data.get("peerDependencies", {}))
                
                # Convert keys to lowercase for case-insensitive matching
                deps_lower = {k.lower(): v for k, v in deps.items()}
                
                # Framework and Tool detection
                if "react" in deps_lower:
                    frameworks.add("React")
                    confidence["React"] = "High"
                if "vite" in deps_lower:
                    frameworks.add("Vite")
                    confidence["Vite"] = "High"
                if "next" in deps_lower:
                    frameworks.add("Next.js")
                    confidence["Next.js"] = "High"
                if "express" in deps_lower:
                    frameworks.add("Express")
                    confidence["Express"] = "High"
                    
                # Node.js Database drivers detection
                if "mongodb" in deps_lower or "mongoose" in deps_lower:
                    databases.add("MongoDB")
                    confidence["MongoDB"] = "High"
                if "pg" in deps_lower:
                    databases.add("PostgreSQL")
                    confidence["PostgreSQL"] = "High"
                if "mysql" in deps_lower or "mysql2" in deps_lower:
                    databases.add("MySQL")
                    confidence["MySQL"] = "High"
                    
            except Exception:
                # Silently skip if package.json is malformed
                pass

        # 2. Python & Python Frameworks
        is_python = False
        if os.path.exists(requirements_path):
            is_python = True
            confidence["Python"] = "High"
        else:
            # Fallback: scan for any Python files in the repository (excluding ignored folders)
            ignore_folders = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if d not in ignore_folders]
                if any(f.endswith('.py') for f in files):
                    is_python = True
                    confidence["Python"] = "Medium"
                    break
                    
        if is_python:
            tech_stack.add("Python")
            project_types.add("Python")
            if "Python" not in confidence:
                confidence["Python"] = "High"
                
            # Scan requirements.txt contents
            if os.path.exists(requirements_path):
                try:
                    with open(requirements_path, 'r', encoding='utf-8', errors='ignore') as f:
                        reqs_content = f.read().lower()
                    
                    # Search for frameworks
                    if "fastapi" in reqs_content:
                        frameworks.add("FastAPI")
                        confidence["FastAPI"] = "High"
                    if "streamlit" in reqs_content:
                        frameworks.add("Streamlit")
                        confidence["Streamlit"] = "High"
                    if "flask" in reqs_content:
                        frameworks.add("Flask")
                        confidence["Flask"] = "High"
                    if "django" in reqs_content:
                        frameworks.add("Django")
                        confidence["Django"] = "High"
                        
                    # Python database drivers detection
                    if "pymongo" in reqs_content or "motor" in reqs_content:
                        databases.add("MongoDB")
                        confidence["MongoDB"] = "High"
                    if "psycopg" in reqs_content or "asyncpg" in reqs_content:
                        databases.add("PostgreSQL")
                        confidence["PostgreSQL"] = "High"
                    if "mysqlclient" in reqs_content or "pymysql" in reqs_content or "mysql-connector" in reqs_content:
                        databases.add("MySQL")
                        confidence["MySQL"] = "High"
                        
                except Exception:
                    pass

        # 3. Docker & Docker Compose
        has_docker = False
        if os.path.exists(dockerfile_path):
            has_docker = True
            confidence["Docker"] = "High"
            
        if os.path.exists(docker_compose_yml) or os.path.exists(docker_compose_yaml):
            has_docker = True
            if "Docker" not in confidence:
                confidence["Docker"] = "High"
            # Explicitly track Docker Compose if needed
            # We can map it to Docker as specified in requirements
            
        if has_docker:
            tech_stack.add("Docker")

        # 4. Environment Variables database check
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                    env_content = f.read().lower()
                
                # Check MongoDB patterns
                if "mongodb://" in env_content or "mongodb+srv://" in env_content or "mongo" in env_content:
                    databases.add("MongoDB")
                    if "MongoDB" not in confidence:
                        confidence["MongoDB"] = "High" if ("mongodb://" in env_content or "mongodb+srv://" in env_content) else "Medium"
                        
                # Check PostgreSQL patterns
                if "postgres://" in env_content or "postgresql://" in env_content or "postgres" in env_content or "pgdatabase" in env_content:
                    databases.add("PostgreSQL")
                    if "PostgreSQL" not in confidence:
                        confidence["PostgreSQL"] = "High" if ("postgres://" in env_content or "postgresql://" in env_content) else "Medium"
                        
                # Check MySQL patterns
                if "mysql://" in env_content or "mysql" in env_content:
                    databases.add("MySQL")
                    if "MySQL" not in confidence:
                        confidence["MySQL"] = "High" if "mysql://" in env_content else "Medium"
            except Exception:
                pass

        # 5. Determine Project Type classification
        if len(project_types) == 1:
            project_type = list(project_types)[0]
        elif len(project_types) > 1:
            project_type = "Multi-stack"
        else:
            # Fallback to language files if no package.json or requirements.txt
            if "Python" in tech_stack:
                project_type = "Python"
            elif "Node.js" in tech_stack:
                project_type = "Node.js"
            else:
                project_type = "Unknown"
                
        return {
            "project_type": project_type,
            "tech_stack": sorted(list(tech_stack)),
            "frameworks": sorted(list(frameworks)),
            "databases": sorted(list(databases)),
            "confidence": confidence
        }
