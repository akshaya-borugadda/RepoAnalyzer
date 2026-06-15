import os
import re
from typing import Dict, Any, List

class SummaryService:
    @staticmethod
    def extract_readme_summary(repo_path: str) -> str:
        """
        Locates and reads the README file of a repository, parsing its initial
        paragraphs to extract a concise description of the codebase.
        """
        readme_names = ["README.md", "readme.md", "README", "readme", "README.txt"]
        readme_path = None
        
        for name in readme_names:
            p = os.path.join(repo_path, name)
            if os.path.exists(p):
                readme_path = p
                break
                
        if not readme_path:
            return ""
            
        try:
            with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Split by lines and parse to find the first descriptive paragraph
            lines = content.split('\n')
            paragraphs = []
            current_para = []
            
            for line in lines:
                line_str = line.strip()
                
                # Check for paragraph boundary
                if not line_str:
                    if current_para:
                        paragraphs.append(" ".join(current_para))
                        current_para = []
                    continue
                
                # Skip headings, blocks, bullet points, lists, or markdown assets
                if line_str.startswith(('#', '>', '!', '[!', '```', '- ', '* ', '1. ')):
                    if current_para:
                        paragraphs.append(" ".join(current_para))
                        current_para = []
                    continue
                    
                # Skip badging badges (e.g., build passing, license badges)
                if line_str.startswith('[![') or (line_str.startswith('[') and '](' in line_str and line_str.endswith(')')):
                    continue
                    
                current_para.append(line_str)
                
            if current_para:
                paragraphs.append(" ".join(current_para))
                
            # Filter paragraphs to find a paragraph with actual explanatory text
            valid_paras = [
                p for p in paragraphs 
                if len(p) > 25 and not p.startswith('<') and not p.startswith('http')
            ]
            
            if valid_paras:
                summary_text = valid_paras[0]
                # Cap the length of the extracted summary
                if len(summary_text) > 300:
                    return summary_text[:297] + "..."
                return summary_text
                
        except Exception:
            pass
        return ""

    @staticmethod
    def generate_project_summary(repo_path: str, tech_info: Dict[str, Any], languages: Dict[str, int]) -> str:
        """
        Assembles a rule-based summary using the extracted README description
        and the detected tech stack metrics.
        """
        readme_desc = SummaryService.extract_readme_summary(repo_path)
        
        project_type = tech_info.get("project_type", "Unknown")
        tech_stack = tech_info.get("tech_stack", [])
        frameworks = tech_info.get("frameworks", [])
        databases = tech_info.get("databases", [])
        
        # Build tech details string
        tech_details = []
        if tech_stack:
            tech_details.append(f"languages/platforms: {', '.join(tech_stack)}")
        if frameworks:
            tech_details.append(f"frameworks: {', '.join(frameworks)}")
        if databases:
            tech_details.append(f"databases: {', '.join(databases)}")
            
        stack_desc = ""
        if tech_details:
            stack_desc = "It is built using " + "; ".join(tech_details) + "."
            
        # Compile response
        summary_lines = []
        if readme_desc:
            summary_lines.append(readme_desc)
            if stack_desc:
                summary_lines.append(stack_desc)
        else:
            # Fallback if no README exists
            top_langs = list(languages.keys())[:3]
            lang_str = f"primarily written in {', '.join(top_langs)}" if top_langs else "without detectable programming languages"
            fallback_desc = f"This is a {project_type} repository, {lang_str}."
            summary_lines.append(fallback_desc)
            if stack_desc:
                summary_lines.append(stack_desc)
                
        return "\n\n".join(summary_lines)

    @staticmethod
    def identify_important_files(repo_path: str) -> List[Dict[str, Any]]:
        """
        Scans all files in the repository and applies heuristic mappings to identify
        key files (entry points, configurations, schemas, routing) with scores.
        """
        important_files = []
        ignore_folders = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
        
        for root, dirs, files in os.walk(repo_path):
            # Exclude ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_folders and d.lower() not in ignore_folders]
            
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path).replace('\\', '/')
                
                file_lower = file.lower()
                rel_path_lower = rel_path.lower()
                
                is_important = False
                file_type = "Source Code"
                purpose = ""
                score = 1
                
                # Check rules sequentially
                if file_lower == 'readme.md':
                    is_important = True
                    file_type = "Documentation"
                    purpose = "Provides project descriptions, configurations, setup guidelines, and project definitions."
                    score = 10
                    
                elif file_lower == 'package.json':
                    is_important = True
                    file_type = "Configuration"
                    purpose = "Defines Node.js dependencies, environment parameters, build scripts, and general metadata."
                    score = 9
                    
                elif file_lower == 'requirements.txt':
                    is_important = True
                    file_type = "Configuration"
                    purpose = "Lists Python dependency requirements necessary to install and run the program."
                    score = 9
                    
                elif file_lower in ('main.py', 'app.py'):
                    is_important = True
                    file_type = "Entrypoint"
                    purpose = "Main Python server script that initiates database connections, mounts routes, and runs the application."
                    score = 9
                    
                elif file_lower in ('server.js', 'index.js'):
                    is_important = True
                    file_type = "Entrypoint"
                    purpose = "Main server driver file launching the Node.js backend application."
                    score = 9
                    
                elif file_lower in ('app.jsx', 'app.tsx'):
                    is_important = True
                    file_type = "Entrypoint (Frontend)"
                    purpose = "Base React component defining layout routing structures and mounting child views."
                    score = 9
                    
                elif 'route' in file_lower or '/routes/' in f"/{rel_path_lower}/":
                    is_important = True
                    file_type = "Routing"
                    purpose = "Specifies API paths, routes, web endpoints, and registers request parameters."
                    score = 8
                    
                elif 'controller' in file_lower or '/controllers/' in f"/{rel_path_lower}/":
                    is_important = True
                    file_type = "Controller"
                    purpose = "Hosts business logic workflows, mapping requests to core services or data schemas."
                    score = 8
                    
                elif 'model' in file_lower or '/models/' in f"/{rel_path_lower}/":
                    is_important = True
                    file_type = "Data Model"
                    purpose = "Declares data schemas, model mappings, collections, database tables, or repository entities."
                    score = 8
                    
                elif 'config' in file_lower or '/config/' in f"/{rel_path_lower}/" or file_lower.endswith(('.toml', '.ini', '.env')):
                    is_important = True
                    file_type = "Configuration"
                    purpose = "Stores settings parameters, runtime environments, external resources keys, or connections."
                    score = 7
                    
                if is_important:
                    important_files.append({
                        "file_path": rel_path,
                        "file_type": file_type,
                        "purpose": purpose,
                        "importance_score": score
                    })
                    
        # Sort by score (descending), then alphabetically by path
        important_files.sort(key=lambda x: (-x["importance_score"], x["file_path"].lower()))
        return important_files
