import os
import re
from typing import Dict, Any, List, Set

class GraphService:
    # Match Python function definitions (e.g. def handle_auth():)
    FUNCTION_PATTERN = re.compile(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', re.MULTILINE)
    
    # Match JS/TS function or component arrow declarations
    JS_ENTITY_PATTERN = re.compile(
        r'^\s*(?:function\s+([a-zA-Z_][a-zA-Z0-9_]*)|const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>)',
        re.MULTILINE
    )

    @staticmethod
    def build_graph(repo_path: str, repo_name: str, api_routes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds a simple JSON knowledge graph representing the nodes and relationships in the codebase.
        
        Args:
            repo_path (str): Local path to the repository.
            repo_name (str): Repository name.
            api_routes (list): API routes found in the repository.
            
        Returns:
            Dict[str, Any]: Object with nodes and edges arrays.
        """
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        
        # Track inserted IDs to guarantee uniqueness
        node_ids: Set[str] = set()
        
        def add_node(node_id: str, label: str, node_type: str) -> None:
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "label": label,
                    "type": node_type
                })
                node_ids.add(node_id)
                
        def add_edge(source: str, target: str, edge_type: str) -> None:
            # Only connect nodes that exist in the registry
            if source in node_ids and target in node_ids:
                edges.append({
                    "source": source,
                    "target": target,
                    "type": edge_type
                })
                
        # 1. Add repository node
        repo_node_id = f"repo_{repo_name}"
        add_node(repo_node_id, repo_name, "repository")
        
        ignore_folders = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
        
        # 2. Walk directory structure to create folders and files nodes
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ignore_folders and d.lower() not in ignore_folders]
            
            rel_root = os.path.relpath(root, repo_path).replace('\\', '/')
            if rel_root == '.':
                rel_root = ""
                
            for folder in dirs:
                folder_rel_path = folder if not rel_root else f"{rel_root}/{folder}"
                folder_node_id = f"folder_{folder_rel_path}"
                add_node(folder_node_id, folder, "folder")
                
                # Link folder to its parent
                parent_node_id = f"folder_{rel_root}" if rel_root else repo_node_id
                add_edge(parent_node_id, folder_node_id, "contains")
                
            for file in files:
                file_rel_path = file if not rel_root else f"{rel_root}/{file}"
                file_node_id = f"file_{file_rel_path}"
                add_node(file_node_id, file, "file")
                
                # Link file to its parent folder
                parent_node_id = f"folder_{rel_root}" if rel_root else repo_node_id
                add_edge(parent_node_id, file_node_id, "contains")
                
                # Check extension to extract sub-file definitions (classes, functions, components)
                _, ext = os.path.splitext(file.lower())
                if ext in ('.py', '.js', '.jsx', '.ts', '.tsx'):
                    try:
                        file_full_path = os.path.join(root, file)
                        with open(file_full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_content = f.read()
                            
                        # Python: extract functions (max 5 to keep graph clean)
                        if ext == '.py':
                            funcs = GraphService.FUNCTION_PATTERN.findall(file_content)
                            for func in funcs[:5]:
                                func_node_id = f"func_{file_rel_path}_{func}"
                                add_node(func_node_id, func, "function")
                                add_edge(file_node_id, func_node_id, "defines")
                                
                        # JS/TS: extract functions/components (max 5)
                        elif ext in ('.js', '.jsx', '.ts', '.tsx'):
                            entities = GraphService.JS_ENTITY_PATTERN.findall(file_content)
                            parsed_names = [name for t in entities for name in t if name]
                            
                            for name in parsed_names[:5]:
                                # React components start with a capital letter
                                node_type = "component" if name[0].isupper() else "function"
                                entity_node_id = f"{node_type}_{file_rel_path}_{name}"
                                add_node(entity_node_id, name, node_type)
                                add_edge(file_node_id, entity_node_id, "defines")
                                
                    except Exception:
                        pass
                        
        # 3. Connect API routes to files that define them
        for route in api_routes:
            method = route["method"]
            path = route["path"]
            file_path = route["file_path"]
            
            api_node_id = f"api_{method}_{path}"
            # Render descriptive label
            add_node(api_node_id, f"{method} {path}", "api")
            
            file_node_id = f"file_{file_path}"
            add_edge(file_node_id, api_node_id, "defines")
            
        # 4. Extract import connections between source files using ImportResolver
        from app.services.import_resolver import ImportResolver
        dep_graph = ImportResolver.build_dependency_graph(repo_path)
        
        for file_rel_path, resolved_imports in dep_graph.items():
            file_node_id = f"file_{file_rel_path}"
            for imported_file in resolved_imports:
                imported_node_id = f"file_{imported_file}"
                add_edge(file_node_id, imported_node_id, "imports")
                                
        return {
            "nodes": nodes,
            "edges": edges
        }
