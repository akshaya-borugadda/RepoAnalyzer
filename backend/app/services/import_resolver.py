import os
import re
from typing import Dict, Any, List, Set

class ImportResolver:
    # Regex expressions for JS/TS imports
    JS_DYNAMIC_IMPORT = re.compile(r'\b(?:import|require)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)')
    JS_ES6_IMPORT = re.compile(r'\bimport\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]')
    JS_SIDE_EFFECT_IMPORT = re.compile(r'\bimport\s+[\'"]([^\'"]+)[\'"]')
    
    # Regex expressions for Python imports
    PY_IMPORT = re.compile(r'\bimport\s+([a-zA-Z_][a-zA-Z0-9_\.]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_\.]*)*)\b')
    PY_FROM_IMPORT = re.compile(r'\bfrom\s+(\.?\??[a-zA-Z_][a-zA-Z0-9_\.]*)\s+import\s+')

    @staticmethod
    def resolve_js_import(src_file: str, target: str, all_files: Set[str]) -> List[str]:
        """
        Resolves a JS/TS import path (relative, aliased, or absolute) to matching files in the repo.
        """
        resolved = []
        src_dir = os.path.dirname(src_file)
        
        # 1. Relative imports (e.g. ./components/Button)
        if target.startswith(('.', '..')):
            target_path = os.path.normpath(os.path.join(src_dir, target)).replace('\\', '/')
            
            # Extensions to test
            extensions = ['', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.jsx', '/index.ts', '/index.tsx']
            for ext in extensions:
                test_path = target_path + ext
                if ext.startswith('/index'):
                    test_path = os.path.normpath(target_path + ext).replace('\\', '/')
                test_path = test_path.strip('/')
                
                if test_path in all_files:
                    resolved.append(test_path)
                    
        # 2. Alias imports (e.g. "@/components/Button")
        elif target.startswith('@/'):
            alias_path = 'src/' + target[2:]
            extensions = ['', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.jsx', '/index.ts', '/index.tsx']
            for ext in extensions:
                test_path = os.path.normpath(alias_path + ext).replace('\\', '/').strip('/')
                if test_path in all_files:
                    resolved.append(test_path)
                    
        # 3. Direct/Root module import checks (e.g. "src/app/main")
        else:
            extensions = ['', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.jsx', '/index.ts', '/index.tsx']
            for ext in extensions:
                test_path = os.path.normpath(target + ext).replace('\\', '/').strip('/')
                if test_path in all_files:
                    resolved.append(test_path)
                    
        return resolved

    @staticmethod
    def resolve_py_import(src_file: str, target_module: str, all_files: Set[str]) -> List[str]:
        """
        Resolves a Python import statement (absolute package or relative dot module) to file paths in the repo.
        """
        resolved = []
        src_dir = os.path.dirname(src_file)
        
        # 1. Relative imports (e.g. from .utils import check)
        if target_module.startswith('.'):
            dots_count = 0
            for char in target_module:
                if char == '.':
                    dots_count += 1
                else:
                    break
                    
            module_name = target_module[dots_count:].replace('.', '/')
            
            # Climb directories based on dots count
            current_dir = src_dir
            for _ in range(dots_count - 1):
                current_dir = os.path.dirname(current_dir)
                
            target_path = os.path.normpath(os.path.join(current_dir, module_name)).replace('\\', '/') if module_name else current_dir
            target_path = target_path.replace('\\', '/')
        else:
            # 2. Absolute imports (e.g. import app.services)
            target_path = target_module.replace('.', '/')
            
        extensions = ['', '.py', '/__init__.py']
        for ext in extensions:
            test_path = os.path.normpath(target_path + ext).replace('\\', '/').strip('/')
            if test_path in all_files:
                resolved.append(test_path)
                
        return resolved

    @staticmethod
    def build_dependency_graph(repo_path: str) -> Dict[str, List[str]]:
        """
        Scans all files in the repository and resolves their imports to build a dependency map.
        
        Returns:
            Dict[str, List[str]]: Map of file_path -> list of imported file_paths in the repo.
        """
        dependencies = {}
        all_files: Set[str] = set()
        ignore_folders = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
        
        # Gather all project file paths relative to repo root
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ignore_folders and d.lower() not in ignore_folders]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path).replace('\\', '/')
                all_files.add(rel_path)
                
        # Parse imports from each source file
        for rel_path in all_files:
            _, ext = os.path.splitext(rel_path.lower())
            if ext not in ('.py', '.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.html'):
                continue
                
            full_path = os.path.join(repo_path, rel_path)
            imports = set()
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    line_stripped = line.strip()
                    
                    # Skip code comments
                    if line_stripped.startswith('#') or line_stripped.startswith('//'):
                        continue
                        
                    # A. Parse Python imports
                    if ext == '.py':
                        # Check "from X import Y"
                        from_match = ImportResolver.PY_FROM_IMPORT.search(line_stripped)
                        if from_match:
                            module_target = from_match.group(1)
                            resolved = ImportResolver.resolve_py_import(rel_path, module_target, all_files)
                            imports.update(resolved)
                            
                        # Check "import X, Y"
                        import_match = ImportResolver.PY_IMPORT.search(line_stripped)
                        if import_match:
                            modules_str = import_match.group(1)
                            for mod in modules_str.split(','):
                                resolved = ImportResolver.resolve_py_import(rel_path, mod.strip(), all_files)
                                imports.update(resolved)
                                
                    # B. Parse JS/TS imports
                    elif ext in ('.js', '.jsx', '.ts', '.tsx'):
                        # Check ES6 import: import X from 'path'
                        es6_match = ImportResolver.JS_ES6_IMPORT.search(line_stripped)
                        if es6_match:
                            resolved = ImportResolver.resolve_js_import(rel_path, es6_match.group(1), all_files)
                            imports.update(resolved)
                            continue
                            
                        # Check dynamic/require import: require('path')
                        dyn_match = ImportResolver.JS_DYNAMIC_IMPORT.search(line_stripped)
                        if dyn_match:
                            resolved = ImportResolver.resolve_js_import(rel_path, dyn_match.group(1), all_files)
                            imports.update(resolved)
                            continue
                            
                        # Check side-effect import: import 'path'
                        side_match = ImportResolver.JS_SIDE_EFFECT_IMPORT.search(line_stripped)
                        if side_match:
                            resolved = ImportResolver.resolve_js_import(rel_path, side_match.group(1), all_files)
                            imports.update(resolved)
                            
                    # C. Stylesheets @import
                    elif ext in ('.css', '.scss'):
                        if '@import' in line_stripped:
                            # Extract path inside quotes
                            quote_match = re.search(r'[\'"]([^\'"]+)[\'"]', line_stripped)
                            if quote_match:
                                target = quote_match.group(1)
                                resolved = ImportResolver.resolve_js_import(rel_path, target, all_files)
                                imports.update(resolved)
                                
            except Exception:
                pass
                
            dependencies[rel_path] = list(imports)
            
        return dependencies
