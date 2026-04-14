"""
Agent system for Carnal 2.0 - enables tool-use and multi-step reasoning
"""
import json
import subprocess
import pathlib
import os
from typing import Any, Dict, List, Optional
import requests

ROOT = pathlib.Path(__file__).parent


class AgentToolkit:
    """Collection of tools Carnal can use."""
    
    def __init__(self, safe_mode: bool = True):
        """
        Initialize toolkit.
        
        Args:
            safe_mode: If True, restrict dangerous commands
        """
        self.safe_mode = safe_mode
        self.execution_log = []
    
    def execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code and return result."""
        try:
            # Restrict dangerous operations in safe mode
            if self.safe_mode:
                forbidden = ['os.system', 'subprocess.run', 'eval', '__import__']
                if any(x in code for x in forbidden):
                    return {"error": "Dangerous code blocked in safe mode", "code": code}
            
            # Pre-import safe modules
            import math
            import json
            
            # Create safe namespace with common modules
            namespace = {
                "math": math,
                "json": json,
                "__name__": "__main__",
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "range": range,
                    "sum": sum,
                    "max": max,
                    "min": min,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "reversed": reversed,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                }
            }
            
            # Capture print output
            output_lines = []
            def captured_print(*args, **kwargs):
                output_lines.append(" ".join(str(a) for a in args))
            namespace["__builtins__"]["print"] = captured_print
            
            # Remove import statements (already have modules available)
            cleaned_code = code.replace("import math", "").replace("import json", "")
            
            exec(cleaned_code, namespace)
            
            self.execution_log.append({"type": "python", "code": code, "status": "success"})
            
            # Return captured output
            output = "\n".join(output_lines) if output_lines else "Code executed"
            return {"success": True, "output": output}
        except Exception as e:
            self.execution_log.append({"type": "python", "code": code, "error": str(e)})
            return {"error": str(e), "code": code}
    
    def execute_command(self, command: str, shell: bool = False) -> Dict[str, Any]:
        """Execute system command."""
        if self.safe_mode:
            # Block dangerous commands
            dangerous = ['rm -rf', 'del /s', 'format', 'shutdown', 'reboot']
            if any(x.lower() in command.lower() for x in dangerous):
                return {"error": "Dangerous command blocked in safe mode"}
        
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            self.execution_log.append({"type": "command", "cmd": command, "status": "success"})
            return {
                "success": True,
                "stdout": result.stdout[:1000],  # Limit output
                "stderr": result.stderr[:1000],
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out (30s limit)"}
        except Exception as e:
            return {"error": str(e), "command": command}
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file (restricted to project directory)."""
        file_path = pathlib.Path(path)
        
        # Security: only allow files in project
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(ROOT.resolve())):
                return {"error": f"Access denied: can only read files in {ROOT}"}
        except Exception:
            return {"error": "Invalid file path"}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            # Limit file size
            if len(content) > 50000:
                content = content[:50000] + "\n... (truncated)"
            
            self.execution_log.append({"type": "read_file", "path": path, "status": "success"})
            return {"success": True, "content": content}
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def write_file(self, path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """Write to a file (restricted to project directory)."""
        file_path = pathlib.Path(path)
        
        # Security: only allow files in project
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(ROOT.resolve())):
                return {"error": f"Access denied: can only write to {ROOT}"}
        except Exception:
            return {"error": "Invalid file path"}
        
        try:
            if append:
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(content)
            else:
                file_path.write_text(content, encoding="utf-8")
            
            self.execution_log.append({"type": "write_file", "path": path, "status": "success"})
            return {"success": True, "path": str(file_path)}
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """List files in directory."""
        dir_path = pathlib.Path(directory) if directory != "." else ROOT
        
        try:
            dir_path = dir_path.resolve()
            if not str(dir_path).startswith(str(ROOT.resolve())):
                return {"error": f"Access denied: can only list {ROOT}"}
        except Exception:
            return {"error": "Invalid path"}
        
        try:
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            
            files = []
            for item in sorted(dir_path.iterdir()):
                files.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {"success": True, "files": files, "path": str(dir_path)}
        except Exception as e:
            return {"error": str(e), "path": directory}
    
    def search_web(self, query: str) -> Dict[str, Any]:
        """Search the web (using free API)."""
        try:
            # Using duckduckgo as free search (no API key needed)
            # This is a simple method; for better results use SerpAPI or similar
            headers = {"User-Agent": "Mozilla/5.0"}
            url = f"https://duckduckgo.com/html/?q={query}"
            
            # This is limited - for production use a proper search API
            return {
                "warning": "Web search is limited without API key",
                "suggestion": "For better search, set SERPAPI_KEY in .env and use search_api_serpapi()",
                "query": query
            }
        except Exception as e:
            return {"error": str(e), "query": query}
    
    def get_logs(self) -> List[Dict]:
        """Get execution logs."""
        return self.execution_log


# Global toolkit instance
toolkit = AgentToolkit(safe_mode=True)


def parse_agent_request(user_message: str) -> Optional[Dict[str, Any]]:
    """
    Check if user is asking for an agent action.
    Returns tool request or None.
    """
    lower = user_message.lower()
    
    # Code execution
    if "run python" in lower or "execute code" in lower:
        return {"type": "python_code_needed"}
    
    # Command execution
    if any(x in lower for x in ["run this command", "execute", "bash", "cmd"]):
        return {"type": "command_needed"}
    
    # File operations
    if "read file" in lower or "show me" in lower:
        return {"type": "file_read_needed"}
    
    if "write file" in lower or "create file" in lower:
        return {"type": "file_write_needed"}
    
    if "list files" in lower or "what files" in lower:
        return {"type": "list_files_needed"}
    
    # Web search
    if "search" in lower or "look up" in lower or "find" in lower:
        return {"type": "web_search_needed"}
    
    return None


def execute_agent_action(action_type: str, **kwargs) -> str:
    """Execute an agent action and return result."""
    
    if action_type == "python":
        code = kwargs.get("code", "")
        result = toolkit.execute_python(code)
    elif action_type == "command":
        command = kwargs.get("command", "")
        result = toolkit.execute_command(command)
    elif action_type == "read_file":
        path = kwargs.get("path", "")
        result = toolkit.read_file(path)
    elif action_type == "write_file":
        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        result = toolkit.write_file(path, content)
    elif action_type == "list_files":
        directory = kwargs.get("directory", ".")
        result = toolkit.list_files(directory)
    elif action_type == "web_search":
        query = kwargs.get("query", "")
        result = toolkit.search_web(query)
    else:
        result = {"error": f"Unknown action type: {action_type}"}
    
    return json.dumps(result, indent=2)
