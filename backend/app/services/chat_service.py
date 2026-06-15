import os
import re
import json
from typing import Dict, Any, List

class ChatService:
    @staticmethod
    def safe_join(separator: str, items: List[Any]) -> str:
        """
        Safely joins a list of elements by converting all items to strings
        and filtering out any None values.
        """
        if not items:
            return ""
        safe_items = [str(item) for item in items if item is not None]
        return separator.join(safe_items)

    @staticmethod
    def search_relevant_context(repo_path: str, question: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Searches relevant source files by question keywords, matching both filenames, path segments,
        and occurrences inside the file contents. Returns the top 5 most relevant files.
        """
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'against', 'between', 'into',
            'through', 'during', 'before', 'after', 'above', 'below', 'from', 'up', 'down', 'in', 'out',
            'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
            'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
            'should', 'now', 'which', 'file', 'files', 'connects', 'connect', 'handle', 'handles', 'does',
            'where', 'what', 'who', 'show', 'list', 'explain', 'get', 'post', 'put', 'delete'
        }
        
        question_lower = question.lower()
        potential_paths = re.findall(r'\b[a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9_]+\b', question_lower)
        
        words = re.findall(r'[a-zA-Z0-9_\-\.\/]+', question_lower)
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        file_scores = {}
        ignore_folders = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ignore_folders and d.lower() not in ignore_folders]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path).replace('\\', '/')
                rel_path_lower = rel_path.lower()
                
                _, ext = os.path.splitext(file.lower())
                if ext not in ('.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.html', '.css', '.md', '.yml', '.yaml', '.sql'):
                    continue
                    
                score = 0
                
                # Path matches
                for pat in potential_paths:
                    if pat in rel_path_lower or rel_path_lower.endswith(pat):
                        score += 200
                        
                # Keyword matches
                for kw in keywords:
                    if kw in rel_path_lower:
                        score += 30
                    if kw == file.lower():
                        score += 40
                        
                # Content matches
                content = ""
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f_obj:
                        content = f_obj.read()
                except Exception:
                    continue
                    
                content_lower = content.lower()
                for kw in keywords:
                    if kw in potential_paths:
                        continue
                    occurrences = content_lower.count(kw)
                    score += min(20, occurrences * 2)
                    
                if score > 0:
                    file_scores[rel_path] = (score, content)
                    
        sorted_files = sorted(file_scores.items(), key=lambda x: x[1][0], reverse=True)
        
        results = []
        for rel_path, (score, content) in sorted_files[:5]:
            results.append({
                "file_path": rel_path,
                "content": content[:2000]
            })
        return results

    @staticmethod
    def answer_question(repo_name: str, question: str) -> Dict[str, Any]:
        """
        Main query responder. Searches top 5 matched files or falls back to rules if Gemini is offline/missing.
        """
        try:
            from app.services.storage_service import StorageService
            from app.core.config import GEMINI_API_KEY
            import google.generativeai as genai
            
            analysis = StorageService.get_analysis(repo_name)
            if not analysis:
                return {
                    "answer": f"No analysis found for repository '{repo_name}'. Please trigger POST `/analyze` for this repository first to index its structure.",
                    "sources": [],
                    "debug_error": "No cached analysis found for this repository."
                }
                
            q = question.lower()
            
            # 1. Rule-based response directly if Gemini key is missing
            if not GEMINI_API_KEY:
                fallback = ChatService.get_rule_based_response(q, analysis, question)
                return {
                    "answer": fallback.get("answer") or "I could not find this information in the analyzed repository.",
                    "sources": fallback.get("sources") or [],
                    "debug_error": "Gemini API key is missing."
                }
                
            # 2. Key is present, run context search and prepare system prompt
            repo_path = analysis.get("repo_path") or ""
            relevant_files = []
            if repo_path and os.path.exists(repo_path):
                relevant_files = ChatService.search_relevant_context(repo_path, question, analysis)
                
            source_context = ""
            if relevant_files:
                for rf in relevant_files:
                    rf_path = rf.get('file_path') or "Unknown"
                    rf_content = rf.get('content') or ""
                    source_context += f"=== FILE: {rf_path} ===\n{rf_content}\n====================\n\n"
            
            # Build flattened repository files tree view for Gemini safely
            flat_files = []
            def get_flat_files(nodes):
                for n in nodes:
                    if not n:
                        continue
                    if n.get("type") == "file":
                        p = n.get("path")
                        if p is not None:
                            flat_files.append(str(p))
                
            if "graph" in analysis and isinstance(analysis["graph"], dict) and "nodes" in analysis["graph"]:
                get_flat_files(analysis["graph"]["nodes"] or [])
                
            flat_files_str = ChatService.safe_join("\n", flat_files[:100])
            if len(flat_files) > 100:
                flat_files_str += f"\n... [and {len(flat_files) - 100} other files]"
                
            system_prompt = (
                "You are an expert developer assistant analyzing a software repository.\n"
                "Your task is to answer user questions about this codebase using only the provided context.\n\n"
                "Here is the repository analysis context:\n"
                f"Repository Name: {repo_name}\n"
                f"Project Classification: {analysis.get('project_type') or 'Unknown'}\n"
                f"Languages: {analysis.get('languages') or {}}\n"
                f"Tech Stack: {analysis.get('tech_stack') or []}\n"
                f"Frameworks: {analysis.get('frameworks') or []}\n"
                f"Databases: {analysis.get('databases') or []}\n"
                f"Project Summary: {analysis.get('summary') or ''}\n\n"
                "Repository File List:\n"
                f"{flat_files_str}\n\n"
                "Important files purposes:\n"
            )
            for f in analysis.get('important_files', []) or []:
                f_path = f.get('file_path') or "Unknown"
                f_type = f.get('file_type') or "Unknown"
                f_purpose = f.get('purpose') or "No purpose defined."
                system_prompt += f"- File: {f_path} | Type: {f_type} | Purpose: {f_purpose}\n"
                
            system_prompt += "\nExposed API routes:\n"
            for r in analysis.get('api_routes', []) or []:
                r_method = r.get('method') or "GET"
                r_path = r.get('path') or "Unknown"
                r_file = r.get('file_path') or "Unknown"
                system_prompt += f"- {r_method} {r_path} in {r_file}\n"
                
            system_prompt += "\nLikely dead or unused files:\n"
            for df in analysis.get('dead_files', []) or []:
                df_path = df.get('file_path') or "Unknown"
                df_reason = df.get('reason') or "No reason provided."
                system_prompt += f"- File: {df_path} | Reason: {df_reason}\n"
                
            if relevant_files:
                system_prompt += f"\nRelevant source file contents:\n{source_context}\n"
            else:
                system_prompt += "\nNo relevant source files were matched for this question. Use the repository layout tree and summary above to answer.\n"
                
            system_prompt += (
                "\nINSTRUCTIONS:\n"
                "1. Answer the question accurately using the context.\n"
                "2. If you cannot find this information in the analyzed repository, or the question is completely outside the codebase scope, reply EXACTLY with this JSON structure:\n"
                "{\n"
                '  "answer": "I could not find this information in the analyzed repository.",\n'
                '  "sources": []\n'
                "}\n"
                "3. Your response MUST be a valid JSON object matching this schema:\n"
                "{\n"
                '  "answer": "Your detailed explanation here, formatted in markdown.",\n'
                '  "sources": [\n'
                "    {\n"
                '      "file_path": "path/to/relevant/file",\n'
                '      "reason": "Why this file is relevant"\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "4. DO NOT wrap your response in markdown code blocks like ```json ... ```. Output raw JSON only.\n"
            )
            
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                f"System Context:\n{system_prompt}\n\nUser Question: {question}",
                generation_config={"response_mime_type": "application/json"}
            )
            
            raw_text = response.text
            cleaned_text = raw_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            parsed_res = json.loads(cleaned_text)
            if "answer" not in parsed_res:
                parsed_res["answer"] = raw_text
                
            sources = []
            if "sources" in parsed_res and isinstance(parsed_res["sources"], list):
                for src in parsed_res["sources"]:
                    if isinstance(src, dict):
                        file_path = src.get("file_path") or ""
                        reason = src.get("reason") or ""
                        if file_path:
                            sources.append({"file_path": file_path, "reason": reason})
                    elif isinstance(src, str):
                        sources.append({"file_path": src, "reason": "Relevant source file"})
            parsed_res["sources"] = sources
            
            return parsed_res
            
        except Exception as err:
            try:
                fallback = ChatService.get_rule_based_response(question.lower(), analysis if 'analysis' in locals() else {}, question)
                return {
                    "answer": fallback.get("answer") or "I could not find this information in the analyzed repository.",
                    "sources": fallback.get("sources") or [],
                    "debug_error": str(err)
                }
            except Exception as inner_err:
                return {
                    "answer": "I could not find this information in the analyzed repository.",
                    "sources": [],
                    "debug_error": f"Outer error: {str(err)}, Inner fallback error: {str(inner_err)}"
                }

    @staticmethod
    def get_rule_based_response(q: str, analysis: Dict[str, Any], question: str) -> Dict[str, Any]:
        """
        Rule-based fallback implementation.
        """
        if not analysis:
            return {
                "answer": "I could not find this information in the analyzed repository.",
                "sources": []
            }
            
        sources: List[Dict[str, str]] = []
        matched_files = []
        matched_routes = []
        
        summary = analysis.get("summary") or ""
        tech_stack = analysis.get("tech_stack") or []
        frameworks = analysis.get("frameworks") or []
        databases = analysis.get("databases") or []
        api_routes = analysis.get("api_routes") or []
        important_files = analysis.get("important_files") or []
        dead_files = analysis.get("dead_files") or []
        
        # 1. Project Overview
        if any(k in q for k in ["explain", "summary", "what does", "what is", "about", "overview"]):
            docs_sources = [
                {"file_path": f.get("file_path") or "Unknown", "reason": "Contains documentation"} 
                for f in important_files if f.get("file_type") == "Documentation"
            ]
            return {
                "answer": f"### Repository Overview\n\n{summary}",
                "sources": docs_sources
            }
            
        # 2. Tech Stack
        if any(k in q for k in ["tech stack", "technology", "technologies", "languages", "built with", "frameworks"]):
            ans_parts = [
                "### Project Technology Stack",
                f"- **Project Type**: {analysis.get('project_type') or 'Unknown'}",
                f"- **Languages & Tools**: {ChatService.safe_join(', ', tech_stack) if tech_stack else 'Not detected'}",
                f"- **Frameworks / Libraries**: {ChatService.safe_join(', ', frameworks) if frameworks else 'None detected'}",
                f"- **Database Platforms**: {ChatService.safe_join(', ', databases) if databases else 'None detected'}"
            ]
            config_sources = [
                {"file_path": f.get("file_path") or "Unknown", "reason": "Configuration guidelines"} 
                for f in important_files if f.get("file_type") == "Configuration"
            ]
            return {
                "answer": ChatService.safe_join("\n", ans_parts),
                "sources": config_sources
            }
            
        # 3. Dead Files
        if any(k in q for k in ["dead", "unused", "disconnected", "orphaned"]):
            if not dead_files:
                return {
                    "answer": "Great news! No dead or unused files were detected in this codebase.",
                    "sources": []
                }
            ans_parts = [
                "### Dead/Unused Files Analysis",
                "The following files were identified as likely unused (no active imports or references found):"
            ]
            for df in dead_files[:15]:
                df_path = df.get("file_path") or "Unknown"
                df_reason = df.get("reason") or "No reason provided."
                df_conf = df.get("confidence") or "medium"
                ans_parts.append(f"- **{df_path}**: {df_reason} *(Confidence: {df_conf})*")
                sources.append({"file_path": df_path, "reason": "Unreferenced file"})
            return {
                "answer": ChatService.safe_join("\n", ans_parts),
                "sources": sources
            }
            
        # 4. API Routes
        if any(k in q for k in ["api", "route", "endpoint", "url", "method", "routes", "endpoints"]):
            if not api_routes:
                return {
                    "answer": "No API routes were identified in the codebase.",
                    "sources": []
                }
            ans_parts = [
                "### Exposed API Routes",
                "Here are the API routing endpoints detected in the codebase:"
            ]
            for route in api_routes[:15]:
                r_method = route.get("method") or "GET"
                r_path = route.get("path") or "Unknown"
                r_file = route.get("file_path") or "Unknown"
                ans_parts.append(f"- `[{r_method}]` `{r_path}` *(defined in {r_file})*")
                sources.append({"file_path": r_file, "reason": f"Defines route {r_path}"})
            return {
                "answer": ChatService.safe_join("\n", ans_parts),
                "sources": sources
            }
            
        # 5. Database Connection
        if any(k in q for k in ["database", "db", "connect", "connection", "sql", "mongo", "postgres", "mysql"]):
            db_keywords = ["db", "conn", "model", "schema", "postgres", "mongo", "mysql", "database", "orm"]
            for f in important_files:
                f_path = f.get("file_path") or ""
                if any(kw in f_path.lower() for kw in db_keywords):
                    matched_files.append(f)
            if matched_files:
                ans_parts = [
                    "### Database Connections & Configuration",
                    "The following files seem associated with database setups, credentials, schemas, or models:"
                ]
                for mf in matched_files:
                    mf_path = mf.get("file_path") or "Unknown"
                    mf_type = mf.get("file_type") or "Unknown"
                    mf_purpose = mf.get("purpose") or "No purpose defined."
                    ans_parts.append(f"- **{mf_path}** ({mf_type}): {mf_purpose}")
                    sources.append({"file_path": mf_path, "reason": mf_purpose})
                return {
                    "answer": ChatService.safe_join("\n", ans_parts),
                    "sources": sources
                }
            else:
                db_info = f" ({ChatService.safe_join(', ', databases)} project)" if databases else ""
                return {
                    "answer": f"I could not locate a dedicated database config or model file{db_info}.",
                    "sources": []
                }
                
        # 5b. Health Score
        if any(k in q for k in ["health", "score", "grade", "report", "quality"]):
            health_score = analysis.get("health_score", 0)
            report = analysis.get("health_report") or {}
            ans_parts = [
                f"### Codebase Health Report: **{health_score}/100**",
                "Here is the breakdown score across the core metrics:",
                f"- **Directory Structure & Layout**: {report.get('structure', 0)}/100",
                f"- **Documentation Completeness**: {report.get('documentation', 0)}/100",
                f"- **Unused Code & Dead Files**: {report.get('unused_code', 0)}/100",
                f"- **Configuration Adequacy**: {report.get('configuration', 0)}/100"
            ]
            doc_configs = [
                {"file_path": f.get("file_path") or "Unknown", "reason": "Doc/Config resource"} 
                for f in important_files 
                if f.get("file_type") in ("Documentation", "Configuration")
            ]
            return {
                "answer": ChatService.safe_join("\n", ans_parts),
                "sources": doc_configs
            }
            
        # 5c. Insights
        if any(k in q for k in ["insight", "insights", "observations", "findings"]):
            insights = analysis.get("insights") or []
            if not insights:
                return {
                    "answer": "No structural insights were identified for this repository.",
                    "sources": []
                }
            ans_parts = ["### Codebase Insights", "Here are key findings and architecture traits:"]
            for ins in insights:
                ans_parts.append(f"- {ins}")
            return {
                "answer": ChatService.safe_join("\n", ans_parts),
                "sources": []
            }
            
        # 6. Feature searches
        features = ["login", "auth", "signup", "register", "user", "payment", "checkout", "search", "config", "test", "middleware"]
        found_features = [f for f in features if f in q]
        
        if found_features:
            feature = found_features[0]
            for f in important_files:
                f_path = f.get("file_path") or ""
                f_purpose = f.get("purpose") or ""
                if feature in f_path.lower() or feature in f_purpose.lower():
                    matched_files.append(f)
            for route in api_routes:
                r_path = route.get("path") or ""
                r_file = route.get("file_path") or ""
                if feature in r_path.lower() or feature in r_file.lower():
                    matched_routes.append(route)
                    
            if matched_files or matched_routes:
                ans_parts = [
                    f"### Matches for Feature: '{feature}'",
                    f"Found files or API endpoints that appear to manage **{feature}** flow:"
                ]
                if matched_files:
                    ans_parts.append("\n**Files:**")
                    for mf in matched_files[:5]:
                        mf_path = mf.get("file_path") or "Unknown"
                        mf_type = mf.get("file_type") or "Unknown"
                        mf_purpose = mf.get("purpose") or "No purpose defined."
                        ans_parts.append(f"- **{mf_path}** ({mf_type}): {mf_purpose}")
                        sources.append({"file_path": mf_path, "reason": mf_purpose})
                if matched_routes:
                    ans_parts.append("\n**API Routes:**")
                    for mr in matched_routes[:5]:
                        mr_method = mr.get("method") or "GET"
                        mr_path = mr.get("path") or "Unknown"
                        mr_file = mr.get("file_path") or "Unknown"
                        ans_parts.append(f"- `[{mr_method}]` `{mr_path}` (in `{mr_file}`)")
                        sources.append({"file_path": mr_file, "reason": "API Endpoint"})
                return {
                    "answer": ChatService.safe_join("\n", ans_parts),
                    "sources": sources
                }
                
        fallback_msg = (
            f"I parsed your question: '{question}'.\n\n"
            f"I couldn't map that to a pre-defined rule. Here is what I can answer:\n"
            f"- **Explain the project** (project summaries and outlines)\n"
            f"- **What is the tech stack?** (languages, frameworks, DBs)\n"
            f"- **Show API routes** (HTTP route directories)\n"
            f"- **Which files are dead?** (unreferenced module tracking)\n"
            f"- **Database connections** (models, configurations)\n"
            f"- Specific code targets (e.g., 'login', 'auth', 'payment')"
        )
        return {
            "answer": fallback_msg,
            "sources": []
        }
